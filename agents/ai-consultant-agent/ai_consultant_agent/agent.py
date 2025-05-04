import os
import json
import logging
from google.adk import Agent
from google.adk.agents import ParallelAgent, SequentialAgent
from typing import List, Optional, Dict, Any

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


async def suggest_development_approach(project_description: str) -> str:
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


async def refactor_code(code_snippet: str, target_principle: Optional[str] = None) -> str:
    """Tool function that suggests refactoring improvements for provided code."""
    return f"""
    Analyze the following code:
    {code_snippet}

    Provide refactoring recommendations focusing on:
    {target_principle if target_principle else "SOLID principles, clean code, and best practices"}

    Identify potential code smells, design weaknesses, and areas for improvement.
    Suggest concrete code changes with examples.
    """


async def generate_tests(code_snippet: str, test_framework: Optional[str] = None) -> str:
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


# --- Individual Agents ---
# Gemini agent
gemini_agent = Agent(
    name='BAID_gemini_agent',
    description='BESKAR.TECH development assistant that helps write code, refactor, create tests, and follow principles like TDD and SOLID.',
    instruction='Help developers write clean, maintainable code following best practices in software development. Provide guidance on testing, refactoring, and implementing design principles.',
    model="gemini-2.0-flash",
    tools=[suggest_development_approach, refactor_code, generate_tests],
    output_key="gemini_response"  # Store result in session state
)

# Claude agent - using direct Vertex AI endpoint string
claude_agent = Agent(
    name='BAID_claude_agent',
    description='BESKAR.TECH development assistant that helps write code, refactor, create tests, and follow principles like TDD and SOLID.',
    instruction='Help developers write clean, maintainable code following best practices in software development. Provide guidance on testing, refactoring, and implementing design principles.',
    model="claude-3-7-sonnet@20250219",  # Using the shortened version that works in your environment
    tools=[suggest_development_approach, refactor_code, generate_tests],
    output_key="claude_response"  # Store result in session state
)

# Parallel execution of both models
parallel_execution = ParallelAgent(
    name="parallel_model_exec",
    sub_agents=[gemini_agent, claude_agent]
)

# Response selector agent - will choose the best response
selector_agent = Agent(
    name="response_selector",
    description="Selects the best response from multiple model outputs",
    instruction="""
    Compare the responses stored in state keys 'gemini_response' and 'claude_response'.
    Select the response that is most comprehensive, well-explained, and helpful.

    Selection criteria:
    - Prefer responses with code examples (look for code blocks with ```)
    - Prefer responses with explanations (containing words like "because" or "reason")
    - Prefer responses with examples or concrete instances
    - Prefer responses with clear structure (multiple headings with # symbols)
    - Longer responses may be more comprehensive, but quality over quantity

    Output only the selected response without any introduction or explanation about your selection process.
    """,
    model="gemini-2.0-flash"  # Using Gemini for selection as it's fast and efficient
)

# Sequential workflow: first run models in parallel, then select best response
multi_agent = SequentialAgent(
    name="BAID_multi_model_agent",
    description="Development assistant using multiple AI models to provide the best coding advice",
    sub_agents=[parallel_execution, selector_agent]
)

# Required variable for ADK CLI
root_agent = multi_agent