# AI Consultant

A cross-platform developer productivity tool combining a FastAPI backend and an IntelliJ IDEA plugin. The goal is to provide in-editor AI-powered code consultation for developers, starting with Kotlin/Java projects in IntelliJ.

---

## Project Structure

- `server/` — Python FastAPI backend
    - Exposes REST API endpoints for code consultation
    - Handles requests from the IntelliJ plugin
    - Current: `/consult` endpoint accepts prompt and file content, returns a simple echo response
- `intelij-plugin/` — IntelliJ IDEA Plugin (Kotlin)
    - Adds a tool window for chat-based code consultation
    - Sends user prompt and current file content to the backend
    - Displays responses in the tool window
    - Current: UI is functional, API call is disabled (placeholder message shown)

---

## End Goal

- Seamless in-editor AI code consultation for developers
- Plugin integration with FastAPI backend for real-time code analysis, suggestions, and explanations
- Support for additional IDEs and languages in the future

---

## Current Implementation Status

- **Server:**
    - FastAPI app exposes `/consult` endpoint (POST)
    - Accepts JSON with `prompt` and `file_content`
    - Returns a status and a preview of the file content (first 200 chars)
- **IntelliJ Plugin:**
    - Tool window UI implemented (Kotlin/Swing)
    - User can enter a prompt and see chat bubbles
    - API integration code is present but currently disabled for initial commit (no compile/runtime errors)

---

## Deployment Pipeline Overview

### Automated Agent & Server Deployment

- **Agent (Vertex AI) Deployment:**
  - Triggered by code changes in `agents/ai-consultant-agent/**` or manually via GitHub Actions UI.
  - Deploys the agent to Vertex AI using `deploy.py`.
  - Captures the remote agent resource ID and writes it to `agent_resource.txt`.
  - Uploads `agent_resource.txt` as a workflow artifact for downstream jobs.

- **Server (Cloud Run) Deployment:**
  - Triggered by code changes in `server/**`, after agent deployment, or manually.
  - Downloads the agent resource artifact and sets `AGENT_HOST` env var for the server.
  - Builds and deploys the FastAPI server to Cloud Run.
  - Signals completion by uploading a `server_deployment_complete` artifact.

### Manual and Automated Controls
- When running the agent workflow manually, you can choose to trigger the server deployment.
- When running the server workflow manually, you must provide the agent resource path as input.

### Artifact Handoff
- The agent workflow uploads the agent resource as an artifact.
- The server workflow downloads this artifact, ensuring the server always points to the latest agent.

See the `agents/ai-consultant-agent/README.md` and `server/README.md` for more details on each component.

---

## Setup & Development

### FastAPI Server
1. `cd server`
2. `pip install -r requirements.txt`
3. `uvicorn main:app --reload`

### IntelliJ Plugin
- Open `intelij-plugin` in IntelliJ IDEA
- Build and run (UI works, API integration to be enabled in future commit)

---

## Contributing
- PRs and issues welcome!

---

## License
Apache 2.0 (see LICENSE)
