# Beskar AI Consultant Agent

This agent functions as an automated AI consultant system specifically designed to provide expert advice and recommendations for AI-related projects. Its primary role is to analyze project requirements and match them with the expertise of available AI models; it achieves this by systematically analyzing project descriptions, evaluating AI requirements, and identifying the best-suited AI solutions based on their capabilities and performance.

## Overview
This agent evaluates project descriptions and recommends the most appropriate AI solutions for the task. Its primary purpose is to serve as an automated AI consulting layer, analyzing project requirements against AI capabilities to optimize AI adoption.

*   Identifies key requirements and AI needs for the project
*   Determines the most suitable AI solution(s) based on capabilities, performance, and project fit
*   Produces clear recommendations with justifications for each selected AI solution
*   Optimizes AI adoption by matching project needs with AI strengths

This sample agent enables a user to submit a project description and receive tailored recommendations for the most appropriate AI solutions to adopt for the project.

## Agent Details

The key features of the Beskar AI Consultant Agent include:

| Feature | Description |
| --- | --- |
| **Interaction Type** | Workflow |
| **Complexity**  | Easy |
| **Agent Type**  | Single Agent |
| **Components**  | Custom Ollama integration with llama3.2 model |
| **Vertical**  | AI Consulting / Adoption |

### Agent architecture:

The agent uses a local Ollama instance running the llama3.2 model to process project descriptions and match them with the appropriate AI solutions based on their capabilities and performance.

## Setup and Installation

1.  **Prerequisites**

    *   Python 3.11+
    *   Google ADK (Agent Development Kit)
    *   Ollama with llama3.2 model installed locally
        *   For installation, please follow the instructions on the official [Ollama website](https://ollama.ai/download)
        *   After installation, download the llama3.2 model: `ollama pull llama3.2`

2.  **Installation**

    ```bash
    # Clone this repository
    git clone https://github.com/your-organization/beskar-ai-consultant-agent.git
    cd beskar-ai-consultant-agent
    # Install the package and dependencies
    pip install -e .
    ```

3.  **Configuration**

    *   Ensure Ollama is running locally on port 11434 (default port)
    *   Set up Google Cloud credentials if using with Vertex AI

        ```bash
        export GOOGLE_GENAI_USE_VERTEXAI=true
        export GOOGLE_CLOUD_PROJECT=<your-project-id>
        export GOOGLE_CLOUD_LOCATION=<your-project-location>
        ```

## Running the Agent

**Using `adk`**

ADK provides convenient ways to bring up agents locally and interact with them.
You may talk to the agent using the CLI:

```bash
adk run ai-consultant-agent
```

Or on a web interface:

```bash
adk web
```

The command `adk web` will start a web server on your machine and print the URL.
You may open the URL, select "baid_agent" in the top-left drop-down menu, and
a chatbot interface will appear on the right. The conversation is initially
blank. Here are some example requests you may ask the AI Consultant Agent:

*   `We need to develop a natural language processing model for our chatbot application.`
*   `We're looking for help designing a computer vision system for our self-driving cars.`

**Programmatic Access**

Below is an example of interacting with the agent using Python:

```python
import os
from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent
from beskar_agent.agent import root_agent

user_input = "We need to develop a natural language processing model for our chatbot application."

runner = InMemoryRunner(agent=root_agent)
session = runner.session_service.create_session(
    app_name=runner.app_name, user_id="test_user"
)
content = UserContent(parts=[Part(text=user_input)])
for event in runner.run(
    user_id=session.user_id, session_id=session.id, new_message=content
):
    for part in event.content.parts:
        print(part.text)
```

### Example Interaction

Below is an example interaction with the Beskar AI Consultant Agent. Note that the exact output
of the agent may vary.

```
user: We need to develop a natural language processing model for our chatbot application.

agent: Based on your project requirements for developing a natural language processing model for a chatbot application, I recommend the following AI solutions:

**Transformers-based Architecture**
- Utilizes pre-trained transformer models for efficient language understanding
- Supports fine-tuning for specific chatbot tasks

Transformers-based architecture is the ideal primary solution for this project due to its state-of-the-art performance in natural language processing tasks. Its ability to be fine-tuned for specific chatbot tasks makes it perfectly suited to develop a robust and accurate NLP model for your application.

**Rule-based Approach**
- Provides a simple and interpretable solution for basic chatbot functionality
- Can be used as a fallback or complementary solution to transformer-based models

Rule-based approach would be an excellent supporting solution on this project, working in conjunction with the transformer-based architecture. This combination will ensure efficient development while providing a robust and accurate NLP model.
```

## CI/CD and Deployment

- The agent can be deployed to Vertex AI using the provided GitHub Actions workflow.
- On deployment, the agent resource ID is written to `agent_resource.txt` and uploaded as a workflow artifact.
- This artifact is consumed by the server deployment workflow to ensure the backend always points to the latest agent.
- Manual and automated triggers are supported (see root README for pipeline details).

### Example: Manual Deployment

1. Trigger the `AI Consultant Agent` workflow from the Actions UI.
2. Optionally choose to trigger the server deployment as part of the workflow run.
3. The workflow will deploy the agent, capture the resource ID, and upload it as an artifact for downstream use.

## Customization

The Beskar AI Consultant Agent can be customized to better suit your requirements:

1.  **Update AI Solutions Information:** Modify the `get_ai_solutions_list()` function to update AI solution information, add new solutions, or adjust capability details.

2.  **Change LLM Model:** Replace the default "llama3.2" model with another Ollama-compatible model by updating the model parameter in the `OllamaLlama` class initialization.

3.  **Customize Prompt Template:** Modify the prompt template in the `generate_content_async` method to adjust how project requirements are analyzed or change the format of recommendations.

4.  **Add Additional Tools:** Expand the agent's capabilities by adding more tools to the agent definition, such as project scheduling or workload balancing functions.