import asyncio
import json
import logging
import os
from typing import AsyncGenerator, Optional
from dataclasses import dataclass

from google.adk.sessions import Session
from google.cloud.aiplatform_v1.services.reasoning_engine_execution_service import ReasoningEngineExecutionServiceClient
from google.cloud.aiplatform_v1 import types
from vertexai import agent_engines
from vertexai.agent_engines import AgentEngine

from baid_server.core.parser.agent_response import parse_ci_response
from baid_server.utils.ci_response_parser import CiResponseParser
from baid_server.config import CIErrorServiceConfigModel # Added import

logger = logging.getLogger(__name__)

# Removed CIErrorServiceConfig dataclass, will use CIErrorServiceConfigModel from config.py

class CIErrorService:

    def __init__(
        self,
        config: CIErrorServiceConfigModel, # Modified: Use CIErrorServiceConfigModel, now required
        execution_client: ReasoningEngineExecutionServiceClient, # Added: Now required
    ):
        self.config = config # Modified: Use injected config
        self.execution_client = execution_client # Modified: Use injected client
        # Internal instantiation of execution_client is removed.

    def get_agent(self) -> AgentEngine:
        logger.debug("Getting ReasoningEngine instance")
        try:
            agent = agent_engines.get(
                self.config.reasoning_engine_app_name,
            )
            logger.debug("Successfully obtained ReasoningEngine instance")
            return agent
        except Exception as e:
            logger.error(f"Failed to get ReasoningEngine instance: {str(e)}", exc_info=True)
            raise

    async def analyze_error(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        request_id: str,
    ) -> AsyncGenerator[str, None]:
        logger.info(f"[{request_id}] Starting CI error analysis for user {user_id}")

        # Get agent instance
        agent: AgentEngine = self.get_agent()

        # Session management
        if not session_id:
            vertex_session: Session = agent.create_session(user_id=user_id)
            session_id = vertex_session["id"]
            logger.info(f"[{request_id}] Created new session {session_id} for user {user_id}")

        # Prepare the stream query request
        try:
            stream_request = types.StreamQueryReasoningEngineRequest(
                name=self.config.agent_engine_id,
                input={
                    "message": prompt,
                    "user_id": user_id,
                    "session_id": session_id,
                }
            )

            # Initialize retry mechanism
            max_retries = 3
            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                try:
                    logger.info(f"[{request_id}] Attempt {retry_count + 1}/{max_retries} to query reasoning engine")
                    stream_response = self.execution_client.stream_query_reasoning_engine(stream_request)

                    full_response = ""
                    processed_events = 0
                    logger.info(f"[{request_id}] Streaming agent response...")

                    for idx, event in enumerate(parse_ci_response(stream_response)):
                        logger.info(f"[{request_id}] Processing event")
                        full_response += str(event)

                        # Detect and surface agent errors
                        try:
                            if isinstance(event, str):
                                event_data = json.loads(event)
                            else:
                                event_data = event

                            if isinstance(event_data, dict) and event_data.get("error_code"):
                                error_msg = f"Agent Error ({event_data['error_code']}): {event_data.get('error_message', 'Unknown error')}"
                                logger.error(f"[{request_id}] Agent returned error: {error_msg}")
                                yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
                                continue
                        except Exception as parse_exc:
                            logger.warning(f"[{request_id}] Could not parse event for error: {parse_exc}")
                            raise Exception(f"JSON parsing error: {str(parse_exc)}")

                        # Process chunks as they come in
                        async for sse_data in CiResponseParser.process_incoming_chunk(event):
                            logger.info(f"[{request_id}] Processed SSE data: {repr(sse_data)}")
                            if sse_data:
                                processed_events += 1
                                yield sse_data
                                await asyncio.sleep(1)

                    # If we processed at least one event without exceptions, mark as success
                    if processed_events > 0:
                        success = True
                    else:
                        raise Exception("No events were processed from the stream response")


                except Exception as e:
                    retry_count += 1
                    logger.error(f"[{request_id}] Attempt {retry_count}/{max_retries} failed: {str(e)}", exc_info=True)
                    if retry_count < max_retries:
                        backoff_time = min(2 ** retry_count, 10)  # Cap at 10 seconds
                        logger.info(f"[{request_id}] Retrying in {backoff_time} seconds...")
                        await asyncio.sleep(backoff_time)
                    else:
                        logger.error(f"[{request_id}] All {max_retries} attempts failed")
                        yield f"data: {{\"error\": \"Internal server error\"}}\n\n"
                        yield "data: [DONE]\n\n"

            if success:
                final_marker = "data: [DONE]\n\n"
                logger.info(f"[{request_id}] Yielding final marker: {final_marker}")
                yield final_marker

        except Exception as e:
            logger.error(f"[{request_id}] Error in analyze_error: {str(e)}", exc_info=True)
            error_msg = str(e)
            logger.error(f"[{request_id}] Final error: {error_msg}")
            yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
            yield "data: [DONE]\n\n"
