import os
import json
import logging
from google.adk import Agent, MultiAgentExecutor
from google.adk.models.lite_llm import LiteLlm
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Software Development Tools ---
def get_development_principles() -> str:
    """Returns a list of software development principles and methodologies."""
    principles = [
        "Test-Driven Development (TDD): Write tests before implementation code.",
        "SOLID Principles: Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion.",
        "Clean Code Practices: Meaningful names, small functions, DRY (Don't Repeat Yourself), comments only when necessary.",
        "Refactoring Techniques: Code smells identification, design pattern implementation, legacy code improvement.",
        "Code Review Best Practices: Readability, maintainability, performance considerations."
    ]
    return "\n".join(principles)


def suggest_development_approach(project_description: str) -> str:
    """Tool function that suggests the best development approach(es) for a project."""
    principles_list = get_development_principles()
    return f"""
    Software development principles and methodologies:
    {principles_list}

    Given the project description: "{project_description}"
    Analyze the requirements and suggest the most appropriate development approach(es).
    Provide specific guidance on how to implement these principles in the context of the project.
    Recommend testing strategies that align with the project goals.
    """


def refactor_code(code_snippet: str, target_principle: Optional[str] = None) -> str:
    """Tool function that suggests refactoring improvements for provided code."""
    return f"""
    Analyze the following code:
    {code_snippet}

    Provide refactoring recommendations focusing on:
    {target_principle if target_principle else "SOLID principles, clean code, and best practices"}

    Identify potential code smells, design weaknesses, and areas for improvement.
    Suggest concrete code changes with examples.
    """


def generate_tests(code_snippet: str, test_framework: Optional[str] = None) -> str:
    """Tool function that generates test cases for provided code."""
    return f"""
    Analyze the following code:
    {code_snippet}

    Generate comprehensive tests focusing on:
    - Unit tests for individual functions/methods
    - Integration tests for component interactions
    - Edge cases and error handling

    Using test framework: {test_framework if test_framework else "appropriate for the language"}
    Follow TDD principles and provide explanations for test coverage considerations.
    """


# --- Selection Logic ---
def select_best_response(responses):
    """
    Basic selector function that selects the best response from multiple agents.

    This implementation uses a simple scoring system based on:
    - Response length (longer responses are often more comprehensive)
    - Presence of code examples
    - Presence of explanations
    """
    logger.info(f"Selecting best response from {len(responses)} responses")

    best_response = None
    max_score = -1

    for agent_name, response in responses.items():
        # Simple scoring heuristic
        score = len(response) * 0.01  # Length contributes to score but not overwhelmingly

        # Code examples are valuable
        if "```" in response:
            score += 10
            # More code blocks are better
            score += response.count("```") * 3

        # Explanations are valuable
        if "because" in response.lower() or "reason" in response.lower():
            score += 8

        # Examples are valuable
        if "example" in response.lower() or "instance" in response.lower():
            score += 5

        # Structure improves readability
        if response.count("#") > 2:  # Markdown headers
            score += 5

        logger.info(f"Agent {agent_name} score: {score:.2f}")

        if score > max_score:
            max_score = score
            best_response = response

    return best_response


# --- Individual Agents ---
# Gemini agent
gemini_agent = Agent(
    name='BAID_gemini_agent',
    description='BESKAR.TECH development assistant that helps write code, refactor, create tests, and follow principles like TDD and SOLID.',
    instruction='Help developers write clean, maintainable code following best practices in software development. Provide guidance on testing, refactoring, and implementing design principles.',
    model="gemini-2.0-flash",
    tools=[suggest_development_approach, refactor_code, generate_tests],
)

# Claude agent
claude_agent = Agent(
    name='BAID_claude_agent',
    description='BESKAR.TECH development assistant that helps write code, refactor, create tests, and follow principles like TDD and SOLID.',
    instruction='Help developers write clean, maintainable code following best practices in software development. Provide guidance on testing, refactoring, and implementing design principles.',
    model=LiteLlm(model="vertex/claude-3-7-sonnet@20250219"),
    tools=[suggest_development_approach, refactor_code, generate_tests],
)

# --- Multi-Agent Executor ---
multi_agent = MultiAgentExecutor(
    name="BAID_multi_model_agent",
    description="Development assistant using multiple AI models to provide the best coding advice",
    agents={"gemini": gemini_agent, "claude": claude_agent},
    selector=select_best_response
)

# Required variable for ADK CLI
root_agent = multi_agent