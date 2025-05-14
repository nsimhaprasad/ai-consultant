import logging
import os
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from baid_server.api.dependencies import get_current_user
from baid_server.models.ci_error import CIErrorRequest
from baid_server.models.agent_response import parse_ci_response
from baid_server.prompts.format import CI_RESPONSE_FORMAT
from baid_server.utils.ci_response_parser import CiResponseParser

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
You are a CI error analyzer.
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
2. A brief explanation of the error
3. A probable fix
Focus on being practical and specific with your solution.

Make sure your response is in the following JSON format:
{CI_RESPONSE_FORMAT}

Stream your response as a series of rfc8259 JSON format only. Do not include any other characters or formatting. Each chunk should be a valid JSON object.
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
        api_endpoint = f"{os.getenv('LOCATION', 'us-central1')}-aiplatform.googleapis.com"
        execution_client = ReasoningEngineExecutionServiceClient(client_options={"api_endpoint": api_endpoint})
        stream_response = execution_client.stream_query_reasoning_engine(stream_request)
        import functools
        import asyncio
        import json
        async def ci_stream():
            full_response = ""
            logger.info(f"[{request_id}] Streaming agent response...")
            loop = asyncio.get_event_loop()
            for idx, event in enumerate(parse_ci_response(stream_response)):
                logger.info(f"[{request_id}] Streaming event #{idx}: Raw event: {repr(event)}")
                full_response += str(event)
                # Detect and surface agent errors
                try:
                    # Try to extract error from JSON event
                    if isinstance(event, str):
                        event_data = json.loads(event)
                    else:
                        event_data = event
                    if isinstance(event_data, dict) and event_data.get("error_code") and event_data.get("error_message"):
                        error_msg = f"Agent Error ({event_data['error_code']}): {event_data['error_message']}"
                        logger.error(f"[{request_id}] Agent returned error: {error_msg}")
                        yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
                        continue
                except Exception as parse_exc:
                    logger.warning(f"[{request_id}] Could not parse event for error: {parse_exc}")
                # Process chunks as they come in - iterate through the async generator
                async for sse_data in CiResponseParser.process_incoming_chunk(event):
                    logger.info(f"[{request_id}] Processed SSE data: {repr(sse_data)}")
                    if sse_data:
                        yield sse_data
                        await asyncio.sleep(1)
            yield "data: [DONE]\n\n"
        return StreamingResponse(ci_stream(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"[{request_id}] Error in CI error analysis: {str(e)}", exc_info=True)
        error_msg = str(e)
        async def error_stream():
            print("error_msg: ", error_msg)
            yield f"data: {{\"solution\": \"Internal server error\", \"explanation\": \"{error_msg}\"}}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")