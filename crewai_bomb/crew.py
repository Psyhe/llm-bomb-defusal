from crewai import Agent, Crew, Task, LLM
from crewai_bomb.tools import ExpertTool, DefuserTool

# # Feel free to import any libraries you need - if needed change requirements.txt
# # In this file it also applies to classes and functions :)

# # YOUR CODE STARTS HERE
# pass
# # YOUR CODE ENDS HERE


# if __name__ == '__main__':
#     # YOUR CODE STARTS HERE
#     pass
#     # YOUR CODE ENDS HERE

def run_crewai_bomb(server_url: str):
    # Initialize tools
    expert_tool = ExpertTool(server_url=server_url)
    defuser_tool = DefuserTool(server_url=server_url)

    # Define agents
    expert_agent = Agent(
        role="Bomb Manual Expert",
        goal="Guide the Defuser by providing accurate bomb module instructions",
        backstory=(
            "You are an expert in bomb defusal manuals, with years of experience guiding defusers remotely. "
            "Your job is to analyze modules and provide precise, calm instructions to ensure success."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[expert_tool]
    )

    defuser_agent = Agent(
        role="Bomb Defuser",
        goal="Carefully execute disarm commands based on expert instructions",
        backstory=(
            "You are the one in the field, holding the bomb. Your task is to execute the commands exactly as given "
            "by the expert, providing updates after each action."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[defuser_tool]
    )

    # Define task
    task = Task(
        description=(
            "You two must work together to disarm the bomb. "
            "Expert: First, retrieve the manual and guide the defuser based on the modules. "
            "Defuser: Report the bomb state and execute the commands step by step."
        ),
        agents=[expert_agent, defuser_agent]
    )

    # LLM config (use gpt-3.5-turbo or whatever model you have)
    llm = LLM(model="gpt-3.5-turbo", temperature=0.2)

    # Create crew
    crew = Crew(
        agents=[expert_agent, defuser_agent],
        tasks=[task],
        llm=llm
    )

    # Kick off!
    result = crew.kickoff()
    print("\n\nFinal result:", result)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Run CrewAI Bomb Defusal")
    parser.add_argument('--url', required=True, help='Server URL (e.g., http://localhost:8080)')
    args = parser.parse_args()

    run_crewai_bomb(args.url)