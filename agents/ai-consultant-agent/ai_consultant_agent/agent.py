import os
import json
from google.adk import Agent
from typing import List, Optional


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


# --- BAID Agent ---
agent = Agent(
    name='BAID_agent',
    description='BESKAR.TECH development assistant that helps write code, refactor, create tests, and follow principles like TDD and SOLID.',
    instruction='Help developers write clean, maintainable code following best practices in software development. Provide guidance on testing, refactoring, and implementing design principles.',
    model="gemini-2.0-flash",  # Use Gemini model
    tools=[suggest_development_approach, refactor_code, generate_tests],
)

# Required variable for ADK CLI
root_agent = agent