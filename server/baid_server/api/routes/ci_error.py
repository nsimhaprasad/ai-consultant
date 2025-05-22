import logging
import os
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from baid_server.api.dependencies import get_current_user
from baid_server.models.ci_error import CIErrorRequest
from baid_server.prompts.format import CI_RESPONSE_FORMAT
# Removed: from baid_server.services.service_factory import ServiceFactory
from baid_server.services.ci_error_service import CIErrorService # Added
from baid_server.services.dependencies import get_ci_error_service # Added

router = APIRouter(tags=["ci"])
logger = logging.getLogger(__name__)

AGENT_RESOURCE_NAME = "projects/742371152853/locations/us-central1/reasoningEngines/7827476054695477248"

@router.post("/api/ci/analyze")
async def analyze_ci_error(
        request: CIErrorRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
        session_id: Optional[str] = Header(None, alias="session_id"),
        service: CIErrorService = Depends(get_ci_error_service) # Added
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
        # Get the CI Error Service via dependency injection
        # Removed: ci_error_service = await ServiceFactory.initialize_ci_error_service()
        
        # Create a streaming response using the CI Error Service
        response_stream = service.analyze_error( # Modified: Use injected service
            prompt=prompt,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id
        )
        
        # Return the streaming response
        return StreamingResponse(response_stream, media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"[{request_id}] Error in CI error analysis: {str(e)}", exc_info=True)
        error_msg = str(e)
        
        async def error_stream():
            logger.error(f"[{request_id}] Error stream: {error_msg}")
            yield f"data: {{\"solution\": \"Internal server error\", \"explanation\": \"{error_msg}\"}}\n\n"
            yield "data: [DONE]\n\n"
            
        return StreamingResponse(error_stream(), media_type="text/event-stream")


async def log_complete_response_from_agent(request_id, stream_response):
    """Log the complete response from the agent while preserving the streaming nature."""
    logger.info(f"[{request_id}] === Logging complete raw response ===")

    # Create a new async generator that logs and forwards chunks
    async def logged_response():
        chunk_count = 0
        try:
            for raw_chunk in stream_response:
                # Log each chunk
                logger.info(f"[{request_id}] RAW CHUNK #{chunk_count}: {repr(raw_chunk)}")
                chunk_count += 1
                # Forward the chunk downstream
                yield raw_chunk
        except Exception as e:
            logger.error(f"[{request_id}] Error in logged_response: {str(e)}")

    # Return the new generator
    return logged_response()