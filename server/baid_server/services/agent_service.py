import asyncio
import logging
import os
import re
from typing import Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass

from google.adk.sessions import VertexAiSessionService, Session
from vertexai import agent_engines
from vertexai.agent_engines import AgentEngine
from google.cloud.aiplatform_v1.services.reasoning_engine_execution_service import ReasoningEngineExecutionServiceClient

from baid_server.db.repositories.message_repository import MessageRepository
from baid_server.db.repositories.session_repository import SessionRepository
from baid_server.utils.response_parser import ResponseParser
from baid_server.prompts import RESPONSE_FORMAT

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


class AgentService:
    def __init__(
            self,
            message_repository: MessageRepository,
            session_repository: SessionRepository,
            response_processor: ResponseParser,
            config: AgentConfig = None,
            session_service: Optional[VertexAiSessionService] = None,
    ):
        self.config = config or AgentConfig()
        self.message_repository = message_repository
        self.session_repository = session_repository
        self.response_processor = response_processor
        api_endpoint = f"{self.config.location}-aiplatform.googleapis.com"
        self.execution_client = ReasoningEngineExecutionServiceClient(client_options={"api_endpoint": api_endpoint})

        # Initialize session service if not provided
        if session_service is None:
            try:
                self.session_service = VertexAiSessionService(
                    project=self.config.project_id,
                    location=self.config.location
                )
                logger.info("Successfully initialized VertexAiSessionService")
            except Exception as e:
                logger.error(f"Failed to initialize VertexAiSessionService: {str(e)}")
                raise
        else:
            self.session_service = session_service

    def get_agent(self) -> AgentEngine:
        logger.debug("Getting AgentEngine instance")
        try:
            agent = agent_engines.get(self.config.agent_engine_id)
            logger.debug("Successfully obtained AgentEngine instance")
            return agent
        except Exception as e:
            logger.error(f"Failed to get AgentEngine instance: {str(e)}", exc_info=True)
            raise

    def create_session(self, user_id: str) -> Session:
        agent = self.get_agent()
        return agent.create_session(user_id=user_id)

    def delete_session(self, user_id: str, session_id: str) -> None:
        self.session_service.delete_session(
            app_name=self.config.reasoning_engine_app_name,
            user_id=user_id,
            session_id=session_id
        )

    async def process_query(
            self,
            user_id: str,
            session_id: Optional[str],
            user_input: str,
            context: Dict[str, Any] = {}
    ) -> AsyncGenerator[str, None]:
        request_id = os.urandom(4).hex()
        logger.info(f"[{request_id}] Processing query for user {user_id}")

        # Get agent instance
        agent: AgentEngine = self.get_agent()

        # Session management
        if not session_id:
            vertex_session = agent.create_session(user_id=user_id)
            session_id = vertex_session["id"]
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

        # Process response using AgentEngine directly
        full_response = ""
        logger.info(f"[{request_id}] Started streaming query")

        max_retries = 3
        retry_count = 0
        success = False

        while retry_count < max_retries and not success:
            try:
                # Use AgentEngine's stream_query method directly
                processed_events = 0
                for event in agent.stream_query(
                        user_id=user_id,
                        session_id=session_id,
                        message=message,
                ):
                    logger.debug(f"[{request_id}] Event from AgentEngine: {event}")

                    # Use dictionary key access instead of hasattr
                    content = event.get('content')
                    if content:
                        parts = content.get('parts')
                        if parts:
                            for part in parts:
                                text = part.get('text')
                                if text:
                                    text_chunk = text
                                    text_chunk = re.sub(r'^```json\s*\n?', '', text_chunk)
                                    text_chunk = re.sub(r'\n?```\s*$', '', text_chunk)
                                    async for sse_data in ResponseParser.process_incoming_chunk(text_chunk):
                                        logger.info(f"[{request_id}] Processed SSE data: {repr(sse_data)}")
                                        if sse_data:
                                            processed_events += 1
                                            yield sse_data
                                    full_response += text_chunk
                                    yield f"data: {text_chunk}\n\n"

                    # Handle final response - check if method exists or if it's a flag
                    is_final = False
                    if hasattr(event, 'is_final_response'):
                        # If it's an object with method
                        is_final = event.is_final_response()
                    elif isinstance(event, dict):
                        # If it's a dictionary, check for a flag
                        is_final = event.get('is_final_response', False)

                    if is_final:
                        logger.info(f"[{request_id}] Received final response")
                        print("final response", full_response)
                        break

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

        # Store assistant response in database
        if full_response:
            logger.info(f"[{request_id}] Storing assistant response in database")
            await self.message_repository.store_message(user_id, session_id, "assistant", full_response)

        yield "data: [DONE]\n\n"