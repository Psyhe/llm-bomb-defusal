import subprocess
import asyncio
import os
import signal
import time
# from agents.prompts import expert_prompt, defuser_prompt
from agents.prompts import  get_expert_prompt, get_defuser_prompt

from game_mcp.game_client import Defuser, Expert
from agents.models import SmollLLM

import re
from typing import List, Optional



OUTPUT_DIR = "experiment_outputs"
TRY_AGAIN = "Try again"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SERVER_CMD = ["python", "-m", "game_mcp.game_server", "--host", "0.0.0.0", "--port", "8080"]

# Expanded grid with temperature, top_p, top_k, and max_new_tokens
PARAM_GRID = [
    {"temperature": 0.3, "top_p": 0.9, "top_k": 600, "max_new_tokens": 900, "style": "standard"},
    {"temperature": 0.7, "top_p": 0.9,  "top_k": 600, "max_new_tokens": 900, "style": "standard"},
    {"temperature": 1.0, "top_p": 0.9,  "top_k": 600, "max_new_tokens": 900, "style": "standard"},
    {"temperature": 0.3, "top_p": 0.9, "top_k": 600, "max_new_tokens": 900, "style": "json"},
    {"temperature": 0.7, "top_p": 0.9,  "top_k": 600, "max_new_tokens": 900, "style": "json"},
    {"temperature": 1.0, "top_p": 0.9,  "top_k": 600, "max_new_tokens": 900, "style": "json"},
    {"temperature": 0.3, "top_p": 0.9, "top_k": 600, "max_new_tokens": 900, "style": "markdown"},
    {"temperature": 0.7, "top_p": 0.9,  "top_k": 600, "max_new_tokens": 900, "style": "markdown"},
    {"temperature": 1.0, "top_p": 0.9,  "top_k": 600, "max_new_tokens": 900, "style": "markdown"},
]

def extract_final_line(prompt_output: str) -> str:
    lines = prompt_output.strip().splitlines()
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        # Remove inline <|im_end|> if present
        if "<|im_end|>" in line:
            line = line.split("<|im_end|>")[0].strip()
        # Skip empty lines and lines starting with "<"
        if line and not line.startswith("<"):
            return line
    return "help"  # fallback if nothing is found

def extract_available_commands(state_text: str) -> str:
    """
    Extracts the 'Available commands' section and everything after it from the given state text.
    """
    marker = "Available commands:"
    index = state_text.find(marker)
    if index == -1:
        return ""  # Marker not found
    return state_text[index:].strip()

def extract_available_commands_list(text: str) -> List[str]:
    """
    Extracts available commands listed after 'Available commands:' in a text block.

    :param text: The input string containing 'Available commands:' and a list of commands.
    :return: A list of command strings.
    """
    lines = text.strip().splitlines()
    commands = []
    start_collecting = False

    for line in lines:
        if line.strip().lower().startswith("available commands:"):
            start_collecting = True
            continue
        if start_collecting:
            if line.strip() == "":
                break
            commands.append(line.strip())
    return commands

def extract_final_instruction(text: str, commands: List[str]) -> Optional[str]:
    """
    Check if the input text contains any of the wire cut commands, and return the correct response.

    :param text: The input line to check.
    :param commands: A list of valid commands (e.g., ['cut wire 1', 'cut wire 2', ...]).
    :return: A formatted response if a match is found; otherwise, None.
    """
    text_lower = text.lower()
    for command in commands:
        if command in text_lower:
            return command
    return TRY_AGAIN
        
def detect_module_type(state_text: str) -> str:
    """
    Detects the module type from the given bomb state text.

    :param state_text: The string containing the bomb state.
    :return: The name of the module detected ("WIRE", "Simon", "Button", "Memory") or "UNKNOWN".
    """
    lower_text = state_text.lower()
    if "wire" in lower_text:
        return "WIRE"
    elif "simon" in lower_text:
        return "Simon"
    elif "memory module" in lower_text:
        return "Memory"
    elif "the button module" in lower_text:
        return "Button"
    else:
        return "UNKNOWN"
    return TRY_AGAIN

async def run_two_agents(defuser_model, expert_model, temperature, top_p, top_k, max_new_tokens, style, run_id):
    defuser_client = Defuser()
    expert_client = Expert()
    server_url = "http://0.0.0.0:8080"

    log_lines = []
    
    attempt=1
    level = 0
    log_module = []
    
    filename = f"{OUTPUT_DIR}/run_{run_id}_T{temperature}_P{top_p}_K{top_k}_M{max_new_tokens}_{style}.txt"

    try:
        await defuser_client.connect_to_server(server_url)
        await expert_client.connect_to_server(server_url)

        log_lines.append("[STEP 1] Connected to server")

        step_count = 0
        while True:
            step_count += 1
            log_lines.append(f"\n===== STEP {step_count} =====")

            bomb_state = await defuser_client.run("state")
            log_lines.append("[DEFUSER sees BOMB STATE]:")
            log_lines.append(bomb_state)
            log_lines.append("\n")

            if "Bomb disarmed!" in bomb_state or "Bomb exploded!" in bomb_state:
                break

            manual_text = await expert_client.run()
            log_lines.append("[EXPERT sees MANUAL]:")
            log_lines.append(manual_text)
            log_lines.append("\n")
            
            module_name = detect_module_type(manual_text)
            
            expert_prompt_fn = get_expert_prompt(style)
            exp_messages = expert_prompt_fn(manual_text, bomb_state)

            # exp_messages = expert_prompt(manual_text, bomb_state)
            log_lines.append("[RECEIVED BY EXPERT]:")
            log_lines.append(str(exp_messages))
            log_lines.append("\n")


            expert_advice = expert_model.generate_response(
                exp_messages,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=True
            )

            log_lines.append("[EXPERT ADVICE to DEFUSER]:")
            log_lines.append(expert_advice)
            log_lines.append("\n")

            print("[EXPERT ADVICE to DEFUSER]:")
            print(expert_advice)
            
            available_commands = extract_available_commands(bomb_state)
            list_of_commands=(extract_available_commands_list(available_commands))


            defuser_prompt_fn = get_defuser_prompt(style)
            def_messages = defuser_prompt_fn(available_commands, expert_advice)
            # def_messages = defuser_prompt(available_commands, expert_advice)
            def_action_raw = defuser_model.generate_response(
                def_messages,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=True
            )

            log_lines.append("[DEFUSER RAW ACTION OUTPUT]:")
            log_lines.append(def_action_raw)
            log_lines.append("\n")
            
            print(def_action_raw)

            final_line = extract_final_line(def_action_raw)
            action = extract_final_instruction(final_line, list_of_commands)
            
            print(f"FINAL LINE: {final_line}")
            print(f"FINAL ACTION: {action}")

            log_lines.append(f"[DEFUSER ACTION DECIDED]: {action}")
            log_lines.append("\n")

            result = await defuser_client.run(action)
            log_lines.append("[SERVER RESPONSE]:")
            log_lines.append(result)
            log_lines.append("\n")        

            if "BOMB SUCCESSFULLY DISARMED" in result or "BOMB HAS EXPLODED" in result:
                # log_module.append("The last module:")
                # log_module.append(module_name)
                # log_module.append(str(max_attempts))
                # log_module.append("\n")
                level += 1
                summary_log = (
                    f'"{filename}",'
                    f'"{temperature}",'
                    f'"{top_p}",'
                    f'"{top_k}",'
                    f'"{max_new_tokens}",'
                    f'"{level}",'
                    f'"{module_name}",'
                    f'"{attempt}",'
                    f'"FAILED"\n'
                )
                
                log_module.append(summary_log)
                
                break
            
            if (action != TRY_AGAIN):
                level += 1
                summary_log = (
                    f'"{filename}",'
                    f'"{temperature}",'
                    f'"{top_p}",'
                    f'"{top_k}",'
                    f'"{max_new_tokens}",'
                    f'"{level}",'
                    f'"{module_name}",'
                    f'"{attempt}",'
                    f'"PASSED"\n'
                )
                
                log_module.append(summary_log)
                attempt = 1
            
            attempt+=1

            print("*******************************")
            print("Attempts:\n")
            print(attempt)
            if attempt >= 7:
                break

    finally:
        await expert_client.cleanup()
        await defuser_client.cleanup()

        # Save full detailed log
        with open(filename, "w") as f:
            f.write("\n".join(log_lines))

        modules = "\n".join(log_module)

        sum_path = os.path.join(OUTPUT_DIR, "experiment_summary.log")
        with open(sum_path, "a") as f:
            f.write(modules)

def launch_server():
    return subprocess.Popen(SERVER_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)


def kill_server(proc):
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

import socket

def wait_for_server(host="0.0.0.0", port=8080, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Server did not start in time.")

async def main():
    print("Starting...")
    defuser_model = SmollLLM("Qwen/Qwen3-0.6B", device="cuda")
    expert_model = SmollLLM("Qwen/Qwen3-0.6B", device="cuda")

    run_id = 0
    for params in PARAM_GRID:
        run_id += 1
        print(f"[RUN {run_id}] Temp: {params['temperature']} | Top-p: {params['top_p']} | Top-k: {params['top_k']} | Max Tokens: {params['max_new_tokens']} | Style: {params['style']}")
        proc = launch_server()
        time.sleep(3)
        wait_for_server()
        try:
            await run_two_agents(
                defuser_model, expert_model,
                temperature=params["temperature"],
                top_p=params["top_p"],
                top_k=params["top_k"],
                max_new_tokens=params["max_new_tokens"],
                style = params["style"],
                run_id=run_id
            )
        finally:
            kill_server(proc)
            time.sleep(4)

if __name__ == "__main__":
    asyncio.run(main())
