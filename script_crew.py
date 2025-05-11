from crewai import Agent, Crew, Task, LLM
from crewai_bomb.tools import ExpertTool, DefuserTool
from dotenv import load_dotenv
import os


def run_crewai_bomb(server_url: str):
    print("Starting run")

    # Initialize tools
    expert_tool = ExpertTool(server_url=server_url)
    defuser_tool = DefuserTool(server_url=server_url)
    print("Tools created")

    # Define agents
    expert_agent = Agent(
        role="Bomb Manual Expert",
        goal="Guide the Defuser by providing accurate bomb module instructions",
        backstory=(
            "You are a calm, experienced bomb defusal expert. You have access to the bomb manual, "
            "and your job is to analyze the module descriptions and provide step-by-step disarm instructions."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[expert_tool]
    )

    defuser_agent = Agent(
        role="Bomb Defuser",
        goal="Carefully execute disarm commands based on expert instructions",
        backstory=(
            "You are in the field with the bomb. Your job is to describe what you see and follow the expert's "
            "instructions exactly. Report status after each step."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[defuser_tool]
    )
    print("Agents created")

    # Define tasks (multi-agent interaction)
    task1 = Task(
        description="Describe the current bomb module you see and ask the expert for instructions.",
        expected_output="A detailed module description and a clear request for guidance.",
        agent=defuser_agent
    )

    task2 = Task(
        description="Use the manual to interpret the defuser's report and provide precise disarm instructions.",
        expected_output="Step-by-step instructions tailored to the described module.",
        agent=expert_agent
    )

    task3 = Task(
        description="Follow the expert's instructions and report the outcome or updated bomb status.",
        expected_output="Confirmation that instructions were followed and the result (e.g., module cleared, error, etc.).",
        agent=defuser_agent
    )

    task4 = Task(
        description="Analyze the defuser's report. If the module is not yet cleared, give follow-up steps. "
                    "If successful, confirm and prepare for next module.",
        expected_output="Next disarm steps or confirmation of module success.",
        agent=expert_agent
    )

    print("Tasks created")

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    llm = LLM(
        provider="openai",
        model="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.2
    )
    # Create Crew
    crew = Crew(
        agents=[expert_agent, defuser_agent],
        tasks=[task1, task2, task3, task4],
        llm=llm,
        verbose=True
    )

    print("Crew created. Kicking off...\n")
    result = crew.kickoff()
    print("\n\nFinal result:", result)


if __name__ == '__main__':
    import argparse

    print("Starting main...")
    parser = argparse.ArgumentParser(description="Run CrewAI Bomb Defusal")
    parser.add_argument('--url', required=True, help='Server URL (e.g., http://localhost:8080)')
    args = parser.parse_args()

    run_crewai_bomb(args.url)
