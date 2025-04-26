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

## Endpoints
- `GET /` - Health check
- `POST /consult` - Placeholder for plugin API calls
