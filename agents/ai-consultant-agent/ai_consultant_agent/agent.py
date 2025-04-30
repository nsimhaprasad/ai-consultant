import os
import json
from google.adk import Agent
from typing import List

# --- AI Solutions Tool ---
def get_ai_solutions_list() -> str:
    """Returns a list of available AI solutions and their capabilities."""
    solutions = [
        "Transformers-based Architecture: Efficient NLP and language understanding, supports fine-tuning.",
        "Rule-based Approach: Simple, interpretable, suitable for basic tasks.",
        "Vision Models: Computer vision, image and video analysis.",
        "Reinforcement Learning Agents: Decision making, game AI, robotics.",
        "Generative Models: Text, image, audio, and code generation."
    ]
    return "\n".join(solutions)

def select_ai_solution(project_description: str) -> str:
    """Tool function that selects the best AI solution(s) for a project."""
    solutions_list = get_ai_solutions_list()
    return f"""
    AI solutions and their capabilities:
    {solutions_list}

    Given the project description: "{project_description}"
    Analyze the requirements and select the most appropriate AI solution(s).
    You can select one or more solutions based on the project needs.
    Suggest a combination of solutions only if the user is intended to have a combination.
    """

# --- Gemini Model Agent ---
agent = Agent(
    name='ai_consultant_agent',
    description='Selects the most appropriate AI solution based on project requirements. For any generic queries, returns a generic LLM Response.',
    instruction='Selects the most appropriate AI solution based on project requirements. For any generic queries, returns a generic LLM Response.',
    model="gemini-2.0-flash",  # Use Gemini model
    tools=[select_ai_solution],
)

# Required variable for ADK CLI
root_agent = agent
