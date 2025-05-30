import asyncio
import json
import logging
import os
import secrets
from dataclasses import dataclass
from typing import Optional, Dict, Any, AsyncGenerator

from vertexai import agent_engines
from vertexai.agent_engines.templates.langchain import LangchainAgent

from baid_server.core.parser.agent_response import parse_langchain_agent_stream
from baid_server.db.repositories.message_repository import MessageRepository
from baid_server.db.repositories.session_repository import SessionRepository
from baid_server.prompts import RESPONSE_FORMAT
from baid_server.utils.response_parser import ResponseParser

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    project_id: str = os.getenv("PROJECT_ID", "742371152853")
    location: str = os.getenv("LOCATION", "us-central1")
    agent_engine_id: str = os.getenv("AGENT_ENGINE_ID", "")

    @property
    def agent_engine_id_only(self) -> str:
        """Get just the ID portion of the agent engine ID."""
        return self.agent_engine_id.split('/')[-1] if self.agent_engine_id else ""

    @property
    def reasoning_engine_app_name(self) -> str:
        """Get the reasoning engine app name."""
        if not self.agent_engine_id_only:
            raise ValueError(
                "AGENT_ENGINE_ID is not set or is invalid. Please set the AGENT_ENGINE_ID environment variable to a valid Vertex AI Agent resource ID."
            )
        return self.agent_engine_id_only


class LangchainAgentService:
    def __init__(
        self,
        message_repository: MessageRepository,
        session_repository: SessionRepository,
        response_processor: ResponseParser,
        config: AgentConfig = None,
    ):
        self.config = config or AgentConfig()
        self.message_repository = message_repository
        self.session_repository = session_repository
        self.response_processor = response_processor


    def get_agent(self) -> LangchainAgent:
        logger.debug("Getting ReasoningEngine instance")
        try:
            agent = agent_engines.LangchainAgent(
                self.config.agent_engine_id,
            )
            logger.debug("Successfully obtained ReasoningEngine instance")
            return agent
        except Exception as e:
            logger.error(f"Failed to get ReasoningEngine instance: {str(e)}", exc_info=True)
            raise

    async def process_query(
            self,
            user_id: str,
            session_id: Optional[str],
            user_input: str,
            context: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        request_id = os.urandom(4).hex()
        logger.info(f"[{request_id}] Processing query for user {user_id}")

        # Get agent instance
        agent: LangchainAgent = self.get_agent()

        if not session_id:
            session_id = secrets.token_hex(32)
            await self.session_repository.store_session_mapping(user_id, session_id)
            logger.info(f"[{request_id}] Created new session {session_id} for user {user_id}")
        else:
            if not await self.session_repository.session_exists(user_id, session_id):
                await self.session_repository.store_session_mapping(user_id, session_id)
                logger.info(f"[{request_id}] Stored existing session {session_id} for user {user_id}")

        # Extract context information
        file_content = context.get("file_content", "")
        is_open = context.get("is_open", False)

        # Prepare message with format instructions
        if is_open:
            message = f"{user_input}\n\nFile content: {file_content}" + "\n" + user_input
        else:
            message = user_input

        message = message + "\n\n" + f"""
        Your response should follow the JSON format specified strictly.
        {RESPONSE_FORMAT}
        """

        # Store user message in database
        await self.message_repository.store_message(user_id, session_id, "user", user_input)

        # Process response
        full_response = ""

        try:
            # Implement retry mechanism - attempt up to 3 times
            max_retries = 3
            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                try:
                    logger.info(
                        f"[{request_id}] Attempt {retry_count + 1}/{max_retries} to query and process reasoning engine response")
                    processed_events = 0

                    for idx, event in enumerate(parse_langchain_agent_stream(agent.stream_query(
                        input=message,
                        config={"configurable": {"session_id": session_id}}
                    ))):
                        logger.info(f"[{request_id}] Streaming event #{idx}: Raw event: {repr(event)}")
                        full_response += str(event)

                        # Detect and surface agent errors
                        try:
                            # Try to extract error from JSON event
                            if isinstance(event, str):
                                event_data = json.loads(event)
                            else:
                                event_data = event

                            if isinstance(event_data, dict) and event_data.get("error_code") and event_data.get(
                                    "error_message"):
                                error_msg = f"Agent Error ({event_data['error_code']}): {event_data['error_message']}"
                                logger.error(f"[{request_id}] Agent returned error: {error_msg}")
                                yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
                                # Don't mark as success but also don't retry - this is an expected error
                                continue
                        except Exception as parse_exc:
                            # JSON parsing error - this is where we want to retry
                            logger.warning(f"[{request_id}] Could not parse event for error: {parse_exc}")
                            raise Exception(f"JSON parsing error: {str(parse_exc)}")

                        # Process chunks as they come in
                        async for sse_data in ResponseParser.process_incoming_chunk(event):
                            logger.info(f"[{request_id}] Processed SSE data: {repr(sse_data)}")
                            if sse_data:
                                processed_events += 1
                                yield sse_data
                                await asyncio.sleep(1)

                    # If we processed at least one event without exceptions, mark as success
                    if processed_events > 0:
                        success = True
                    else:
                        # No events processed, consider this a failed attempt
                        raise Exception("No events were processed from the stream response")

                except Exception as e:
                    retry_count += 1
                    logger.error(
                        f"[{request_id}] Error in query or processing (attempt {retry_count}/{max_retries}): {str(e)}")

                    # Clear the response for retry
                    full_response = ""

                    if retry_count >= max_retries:
                        # If we've exhausted all retries, inform the client
                        logger.error(f"[{request_id}] Max retries ({max_retries}) reached, giving up")
                        yield f"data: {{\"error\": \"Failed after {max_retries} attempts. Last error: {str(e)}\"}}\n\n"
                        # Send final markers even after error
                        session_data = f"data: {{\"session_id\": \"{session_id}\"}}\n\n"
                        yield session_data
                        yield "data: [DONE]\n\n"
                        return

                    # Wait before retrying (exponential backoff)
                    backoff_time = 2 ** retry_count  # 2, 4, 8 seconds
                    logger.info(f"[{request_id}] Waiting {backoff_time} seconds before retry")
                    await asyncio.sleep(backoff_time)



            # Only send session_id and final marker if we had a successful processing
            if success:
                # Send session_id and final marker
                session_data = f"data: {{\"session_id\": \"{session_id}\"}}\n\n"
                logger.info(f"[{request_id}] Yielding session data: {session_data}")
                yield session_data

                final_marker = "data: [DONE]\n\n"
                logger.info(f"[{request_id}] Yielding final marker: {final_marker}")
                yield final_marker
        except Exception as e:
            print("Error in streaming response", e)
            logger.error(f"[{request_id}] Error in streaming response: {str(e)}", exc_info=True)
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            yield "data: [DONE]\n\n"