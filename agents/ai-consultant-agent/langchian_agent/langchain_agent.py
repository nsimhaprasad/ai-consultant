import os
from typing import Optional

from langchain_google_vertexai import HarmBlockThreshold, HarmCategory
from vertexai import agent_engines
from . import TDD_PROMPT, SOLID_PRINCIPLES_PROMPT, CODE_REVIEW_BEST_PRACTICES, CLEAN_CODE_PROMPT, REFACTORING_BEST_PRACTICES
model = "gemini-2.5-pro-preview-03-25"

def get_session_history(session_id: str):
    from langchain_google_firestore import FirestoreChatMessageHistory
    from google.cloud import firestore


    client = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
    return FirestoreChatMessageHistory(
        client=client,
        session_id=session_id,
        collection="session_history",
        encode_message=False,
    )


safety_settings = {
    HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}


model_kwargs = {
    "safety_settings": safety_settings,
}

system_prompt = """
Your name is BAID agent. 
You are BESKAR.TECH development assistant that helps write code, refactor, create tests, and follow principles like TDD and SOLID.
Help developers write clean, maintainable code following best practices in software development. Provide guidance on testing, refactoring, and implementing design principles.
"""

def get_development_principles() -> str:
    """Returns a list of software development principles and methodologies."""
    principles = [
        TDD_PROMPT,
        SOLID_PRINCIPLES_PROMPT,
        CLEAN_CODE_PROMPT,
        REFACTORING_BEST_PRACTICES,
        CODE_REVIEW_BEST_PRACTICES
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

if not os.getenv("PROJECT_ID"):
    raise ValueError("PROJECT_ID environment variable is required for LangchainAgent")

langchain_agent = agent_engines.LangchainAgent(
    model=model,
    system_instruction=system_prompt,
    model_kwargs=model_kwargs,
    tools=[suggest_development_approach, refactor_code, generate_tests],
    chat_history=get_session_history,
)
