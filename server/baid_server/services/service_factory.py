import os
import logging
from typing import Optional, TypeVar, Generic, Type

from google.adk.sessions import VertexAiSessionService

from baid_server.services.agent_service import AgentService, AgentConfig
from baid_server.services.ci_error_service import CIErrorService, CIErrorServiceConfig
from baid_server.db.repositories.message_repository import MessageRepository
from baid_server.db.repositories.session_repository import SessionRepository
from baid_server.services.langchain_agent_service import LangchainAgentService
from baid_server.utils.response_parser import ResponseParser
from baid_server.db.database import get_db_pool

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ServiceFactory(Generic[T]):
    _agent_service: Optional[AgentService] = None
    _ci_error_service: Optional[CIErrorService] = None

    @classmethod
    async def initialize_agent_service(cls) -> AgentService:
        if cls._agent_service is None:
            logger.info("Initializing agent service")
            db_pool = await get_db_pool()
            
            cls._agent_service = AgentService(
                config=AgentConfig(
                    agent_engine_id=os.getenv("AGENT_ENGINE_ID", ""),
                    project_id=os.getenv("PROJECT_ID", ""),
                    location=os.getenv("LOCATION", ""),
                ),
                session_service=VertexAiSessionService (
                    project=os.getenv("PROJECT_ID", ""),
                    location=os.getenv("LOCATION", "")
                ),
                message_repository=MessageRepository(db_pool=db_pool),
                session_repository=SessionRepository(db_pool=db_pool),
                response_processor=ResponseParser()
            )
            logger.info("Agent service initialized")
        
        return cls._agent_service

    @classmethod
    def get_agent_service(cls) -> AgentService:
        if cls._agent_service is None:
            raise RuntimeError("AgentService not initialized")
        return cls._agent_service

    @classmethod
    async def initialize_ci_error_service(cls) -> CIErrorService:
        if cls._ci_error_service is None:
            logger.info("Initializing CI Error service")
            cls._ci_error_service = CIErrorService(
                config=CIErrorServiceConfig(
                    agent_engine_id=os.getenv("AGENT_ENGINE_ID", ""),
                    project_id=os.getenv("PROJECT_ID", ""),
                    location=os.getenv("LOCATION", "")
                )
            )
            logger.info("CI Error service initialized")
        return cls._ci_error_service

    @classmethod
    def get_ci_error_service(cls) -> CIErrorService:
        if cls._ci_error_service is None:
            raise RuntimeError("CIErrorService not initialized")
        return cls._ci_error_service

    @classmethod
    def reset(cls) -> None:
        cls._agent_service = None
        cls._ci_error_service = None
