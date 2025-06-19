# BAID Server

A FastAPI-based server for the BAID (Beskar AI) project.

## Setup

### Prerequisites

- Python 3.12 or higher
- [Poetry](https://python-poetry.org/) for dependency management

### Installation

1. Clone the repository
2. Install dependencies using Poetry:

```bash
poetry install
```

### Development

To run the server locally during development:

```bash
poetry run uvicorn baid_server.main:app --reload --host 0.0.0.0 --port 8080
```

### Docker

Build and run using Docker:

```bash
# Build the Docker image
docker build -t baid-server .

# Run the container
docker run -p 8080:8080 baid-server
```

## Project Structure

- `baid_server/` - Main package directory
  - `main.py` - FastAPI application entry point
  - `api/routes/` - API route handlers
    - `sync.py` - Sync API for baid-sync tool
  - `services/` - Service modules
    - `sync_service.py` - Google Cloud Storage sync service
  - `models/` - Pydantic models
    - `sync.py` - Sync request/response models

## CI/CD and Artifact Integration

- The server deployment workflow downloads the latest agent resource artifact produced by the agent deployment workflow.
- The agent resource ID is used to set the `AGENT_HOST` environment variable for Cloud Run.
- The workflow supports both automatic triggers (after agent deployment) and manual runs (with agent path input).
- After deployment, a completion artifact is uploaded for workflow tracking.

### Example: Manual Server Deployment

1. Trigger the `Server Deploy` workflow from the Actions UI.
2. Provide the agent resource path as input if running manually.
3. The workflow will download the artifact, build and deploy the server, and upload a completion signal.

# Python Server Backend

This is the backend server for the IntelliJ plugin. It uses FastAPI for handling HTTP requests.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### Core Endpoints
- `GET /` - Server health check and status
- `GET /health` - Detailed health check for Cloud Run
- `POST /api/consult` - AI consultation endpoint for IntelliJ plugin

### Authentication
- `GET /api/auth/google-login` - Google OAuth callback
- `GET /api/auth/session` - Session polling for OAuth
- `POST /api/auth/api-key` - API key authentication

### Sync API (for baid-sync tool)
- `POST /api/sync/signed-url` - Get signed URL for compressed archive upload to GCS
- `GET /api/sync/status` - Sync service status and configuration

### Other APIs
- Session management (`/api/sessions/*`)
- User management (`/api/users/*`)
- Waitlist (`/api/waitlist`)
- CI error analysis (`/api/ci-error/*`)

## Environment Variables

### Required
- `JWT_SECRET` - Secret for JWT token signing
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `DATABASE_URL` - PostgreSQL connection string

### Optional
- `GCS_SYNC_BUCKET` - Google Cloud Storage bucket for sync (default: "baid-sync-storage")
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to GCS service account key
- `AGENT_ENGINE_ID` - Vertex AI agent engine ID
