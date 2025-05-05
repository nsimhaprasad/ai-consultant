import os
import json
import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
from google.adk import Agent as GeminiAgent
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configurations
GEMINI_MODEL = "gemini-2.0-flash"

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


def generate_code(language: str, description: str = "A simple program") -> str:
    """Tool function that generates code in the specified programming language."""
    return f"""
    Generate clean, well-documented code in {language} for:

    {description}

    Follow best practices for {language}, including:
    - Proper naming conventions
    - Good documentation/comments
    - Appropriate error handling
    - Modular design

    Provide a complete, working example with explanations of key components.
    """
from google.adk.models.anthropic_llm import Claude # Import needed for registration
from google.adk.models.registry import LLMRegistry # Import needed for registration
LLMRegistry.register(Claude)

# --- Gemini Agent Implementation (single model version) ---
root_agent = GeminiAgent(
    name='gemini_agent',
    description='BESKAR.TECH development assistant using Gemini',
    instruction='''
    Help developers write clean, maintainable code following best practices in software development. 
    Provide guidance on testing, refactoring, and implementing design principles.

    When asked to generate code, always provide a complete, working example with explanations.
    If asked for a specific language like Java, Python, etc., generate code in that language.

    Always respond with detailed, helpful answers even for simple requests.
    Never return empty or minimal responses.

    For "Generate sample Java code" requests, create a complete working Java example 
    with proper class structure, including a main method, comments, and standard Java conventions.
    ''',
    model='claude-3-5-sonnet-v2@20241022',
    tools=[suggest_development_approach, refactor_code, generate_tests, generate_code]
)