import subprocess
import asyncio
import os
import signal
import time
from agents.prompts import expert_prompt, defuser_prompt
from game_mcp.game_client import Defuser, Expert
from agents.models import SmollLLM

import re
from typing import List, Optional


OUTPUT_DIR = "experiment_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SERVER_CMD = ["python", "-m", "game_mcp.game_server", "--host", "0.0.0.0", "--port", "8080"]

# Expanded grid with temperature, top_p, top_k, and max_new_tokens
PARAM_GRID = [
    {"temperature": 0.3, "top_p": 0.95, "top_k": 1000, "max_new_tokens": 1000},
    {"temperature": 0.7, "top_p": 0.9,  "top_k": 1000, "max_new_tokens": 1000},
    {"temperature": 1.0, "top_p": 0.8,  "top_k": 1000, "max_new_tokens": 1000},
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
    return "Try again"

async def run_two_agents(defuser_model, expert_model, temperature, top_p, top_k, max_new_tokens, run_id):
    defuser_client = Defuser()
    expert_client = Expert()
    server_url = "http://0.0.0.0:8080"

    log_lines = []
    
    max_attempts=5

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

            exp_messages = expert_prompt(manual_text, bomb_state)
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

            def_messages = defuser_prompt(available_commands, expert_advice)
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
                break
            
            max_attempts-=1
            log_lines.append("\n")
            log_lines.append(f"[ATTEMPT]: {max_attempts}")

            print("*******************************")
            print("Attempts:\n")
            print(max_attempts)
            if max_attempts <= 0:
                break

    finally:
        await expert_client.cleanup()
        await defuser_client.cleanup()

        filename = f"{OUTPUT_DIR}/run_{run_id}_T{temperature}_P{top_p}_K{top_k}_M{max_new_tokens}.txt"
        with open(filename, "w") as f:
            f.write("\n".join(log_lines))


def launch_server():
    return subprocess.Popen(SERVER_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)

def kill_server(proc):
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)


async def main():
    print("Starting...")
    defuser_model = SmollLLM("Qwen/Qwen3-0.6B", device="cuda")
    expert_model = SmollLLM("Qwen/Qwen3-0.6B", device="cuda")

    run_id = 0
    for params in PARAM_GRID:
        run_id += 1
        print(f"[RUN {run_id}] Temp: {params['temperature']} | Top-p: {params['top_p']} | Top-k: {params['top_k']} | Max Tokens: {params['max_new_tokens']}")
        proc = launch_server()
        time.sleep(3)
        try:
            await run_two_agents(
                defuser_model, expert_model,
                temperature=params["temperature"],
                top_p=params["top_p"],
                top_k=params["top_k"],
                max_new_tokens=params["max_new_tokens"],
                run_id=run_id
            )
        finally:
            kill_server(proc)
            time.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
