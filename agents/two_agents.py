import asyncio

from agents.prompts import expert_prompt, defuser_prompt
from game_mcp.game_client import Defuser, Expert
from agents.models import HFModel, SmollLLM


async def run_two_agents(
        defuser_model: HFModel,
        expert_model: HFModel,
        server_url: str = "http://0.0.0.0:8080",
        max_new_tokens: int = 50
) -> None:
    """
    Main coroutine that orchestrates two LLM agents (Defuser and Expert)
    interacting with the bomb-defusal server.

    :param defuser_model: The HFModel for the Defuser's role.
    :param expert_model: The HFModel for the Expert's role.
    :param server_url: The URL where the bomb-defusal server is running.
    :param max_new_tokens: Max tokens to generate for each LLM response.
    """
    defuser_client = Defuser()
    expert_client = Expert()

    try:
        # 1) Connect both clients to the same server
        await defuser_client.connect_to_server(server_url)
        await expert_client.connect_to_server(server_url)

        while True:
            # 2) Defuser checks the bomb's current state
            bomb_state = await defuser_client.run("state")
            print("[DEFUSER sees BOMB STATE]:")
            print(bomb_state)

            if "Bomb disarmed!" in bomb_state or "Bomb exploded!" in bomb_state:
                break

            # 3) Expert retrieves the relevant manual text
            manual_text = await expert_client.run()
            print("[EXPERT sees MANUAL]:")
            print(manual_text)

            # 4) Expert LLM uses the manual text + defuser’s question (bomb_state)
            #    to generate instructions
            print("before prompt")
            print("**************")
            exp_messages = expert_prompt(manual_text, bomb_state)
            print("after")
            # expert_advice = expert_model.generate_response(
            #     exp_messages,
            #     max_new_tokens=max_new_tokens,
            #     temperature=0.7,
            #     top_p=0.9,
            #     top_k=50,
            #     do_sample=True
            # )
            
            expert_advice = expert_model.generate_response(
                exp_messages,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                top_p=0.9,
                top_k=50,
                do_sample=True
            )

            print("=---------------------")
            print("\n[EXPERT ADVICE to DEFUSER]:")
            print(expert_advice)

            # 5) Defuser LLM uses the bomb state + expert advice to pick a single action
            def_messages = defuser_prompt(bomb_state, expert_advice)
            def_action_raw = defuser_model.generate_response(
                def_messages,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                top_p=0.9,
                top_k=50,
                do_sample=True
            )

            # 6) Attempt to extract a known command from def_action_raw
            #    If no recognized command is found, default to "help"
            action = "help"
            for line in def_action_raw.splitlines():
                line = line.strip().lower()
                if line.startswith(("cut", "press", "hold", "release", "help", "state")):
                    action = line.strip()
                    break

            print("\n[DEFUSER ACTION DECIDED]:", action)

            # 7) Send that action to the server
            result = await defuser_client.run(action)
            print("[SERVER RESPONSE]:")
            print(result)
            print("-" * 60)

            if "BOMB SUCCESSFULLY DISARMED" in result or "BOMB HAS EXPLODED" in result:
                break
    finally:
        await expert_client.cleanup()
        await defuser_client.cleanup()


if __name__ == "__main__":

    defuser_checkpoint = "HuggingFaceTB/SmolLM-135M-Instruct"
    expert_checkpoint = "HuggingFaceTB/SmolLM-135M-Instruct"

    # defuser_checkpoint = "Qwen/Qwen3-0.6B"
    # expert_checkpoint = "Qwen/Qwen3-0.6B"

    defuser_model = SmollLLM(defuser_checkpoint, device="cuda")
    expert_model = SmollLLM(expert_checkpoint, device="cuda")

    asyncio.run(
        run_two_agents(
            defuser_model=defuser_model,
            expert_model=expert_model,
            server_url="http://0.0.0.0:8080",
            max_new_tokens=50
        )
    )
