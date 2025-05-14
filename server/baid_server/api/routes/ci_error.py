import logging
import os
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from baid_server.api.dependencies import get_current_user
from baid_server.models.ci_error import CIErrorRequest

# --- Vertex AI ADK imports ---
from vertexai import agent_engines
from google.cloud.aiplatform_v1.services.reasoning_engine_execution_service import ReasoningEngineExecutionServiceClient
from google.cloud.aiplatform_v1 import types

router = APIRouter(tags=["ci"])
logger = logging.getLogger(__name__)

AGENT_RESOURCE_NAME = "projects/742371152853/locations/us-central1/reasoningEngines/7827476054695477248"

@router.post("/api/ci/analyze")
async def analyze_ci_error(
        request: CIErrorRequest,
        current_user: Dict[str, Any] = Depends(get_current_user)
):
    request_id = os.urandom(4).hex()
    logger.info(f"[{request_id}] === Starting CI error analysis request ===")
    user_id = current_user["sub"]
    prompt = f"""
I'm facing an error in my CI pipeline. Please help me fix it.

## Command
```
{request.command}
```

## Standard Output
```
{request.stdout}
```

## Error Output
```
{request.stderr}
```

Please analyze this error and provide a solution. Focus on the specific issue in the CI pipeline and be very actionable.
Your response should include:
1. A clear explanation of what went wrong
2. A specific solution to fix the error
3. Code examples showing the fix if appropriate
Focus on being practical and specific with your solution.
"""
    try:
        # Get the agent engine
        agent = agent_engines.get(AGENT_RESOURCE_NAME)
        # Create a session for this user/request
        session = agent.create_session(user_id=user_id)
        session_id = session["id"]
        logger.info(f"[{request_id}] Created agent session: {session_id}")
        # Prepare the message
        message = prompt
        # Prepare the stream query request
        stream_request = types.StreamQueryReasoningEngineRequest(
            name=AGENT_RESOURCE_NAME,
            input={
                "message": message,
                "user_id": user_id,
                "session_id": session_id,
            }
        )
        execution_client = ReasoningEngineExecutionServiceClient()
        stream_response = execution_client.stream_query_reasoning_engine(stream_request)
        import functools
        import asyncio
        import json
        async def ci_stream():
            logger.info(f"[{request_id}] Streaming agent response...")
            loop = asyncio.get_event_loop()
            def get_chunks():
                for chunk in stream_response:
                    yield chunk
            chunk_iter = get_chunks()
            while True:
                chunk = await loop.run_in_executor(None, lambda: next(chunk_iter, None))
                if chunk is None:
                    break
                chunk_dict = chunk._pb.__class__.to_dict(chunk._pb)
                logger.debug(f"[{request_id}] Agent chunk: {json.dumps(chunk_dict)[:200]}")
                if "error_code" in chunk_dict and "error_message" in chunk_dict:
                    error_msg = f"Agent Error ({chunk_dict['error_code']}): {chunk_dict['error_message']}"
                    logger.error(f"[{request_id}] Agent returned error: {error_msg}")
                    yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
                    continue
                content = chunk_dict.get("data", "") or chunk_dict.get("content", "")
                if content:
                    yield f"data: {{\"solution\": {json.dumps(content)} }}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(ci_stream(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"[{request_id}] Error in CI error analysis: {str(e)}", exc_info=True)
        error_msg = str(e)
        async def error_stream():
            yield f"data: {{\"solution\": \"Internal server error\", \"explanation\": \"{error_msg}\"}}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")