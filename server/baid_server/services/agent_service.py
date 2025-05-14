import asyncio
import json
import logging
import os
import re
from typing import Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass

from google.adk.sessions import VertexAiSessionService, Session
from vertexai import agent_engines
from vertexai.agent_engines import AgentEngine
from google.cloud.aiplatform_v1.services.reasoning_engine_execution_service import ReasoningEngineExecutionServiceClient
from google.cloud.aiplatform_v1 import types

from baid_server.db.repositories.message_repository import MessageRepository
from baid_server.db.repositories.session_repository import SessionRepository
from baid_server.models.agent_response import parse_agent_stream
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
            vertex_session: Session = agent.create_session(user_id=user_id)
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

        # Process response
        full_response = ""

        try:
            # Stream the response using the stream_query method
            # print("Started streaming query", agent.operation_schemas())

            stream_request = types.StreamQueryReasoningEngineRequest(
                name=self.config.agent_engine_id,
                input={
                    "message": message,
                    "user_id": user_id,  # Add user ID to the input
                    "session_id": session_id,  # Add session ID to the input
                }
            )

            stream_response = self.execution_client.stream_query_reasoning_engine(stream_request)

            for idx, event in enumerate(parse_agent_stream(stream_response)):
                logger.info(f"[{request_id}] Streaming event #{idx}: Raw event: {repr(event)}")
                print(f"[{request_id}] Streaming event #{idx}: Raw event: {repr(event)}")
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
                # Process chunks as they come in
                sse_data = await ResponseParser.process_incoming_chunk(event)
                logger.info(f"[{request_id}] Processed SSE data: {repr(sse_data)}")
                if sse_data:
                    yield sse_data
                    await asyncio.sleep(1)

            # Send session_id and final marker
            session_data = f"data: {{\"session_id\": \"{session_id}\"}}\n\n"
            logger.info(f"[{request_id}] Yielding session data: {session_data}")
            yield session_data

            final_marker = "data: [DONE]\n\n"
            logger.info(f"[{request_id}] Yielding final marker: {final_marker}")
            yield final_marker

            # Store the complete response
            await self.message_repository.store_message(user_id, session_id, "agent", full_response.strip())

        except Exception as e:
            print("Error in streaming response", e)
            logger.error(f"[{request_id}] Error in streaming response: {str(e)}", exc_info=True)
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            yield "data: [DONE]\n\n"