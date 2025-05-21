"""Dependency providers for services."""
from fastapi import Depends

from baid_server.db.repositories.tenant_repository import TenantRepository
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.services.tenant_service import TenantService
from baid_server.services.api_key_service import ApiKeyService
# Import centralized repository dependencies
from baid_server.db.dependencies import (
    get_tenant_repository_dependency,
    get_user_repository_dependency,
    get_message_repository_dependency,
    get_session_repository_dependency,
    get_waitlist_repository_dependency, # Added
    get_global_settings_repository_dependency, # Added
)
# Service Imports
from baid_server.services.tenant_service import TenantService
from baid_server.services.api_key_service import ApiKeyService
from baid_server.services.auth_service import AuthService
from baid_server.services.agent_service import AgentService
from baid_server.services.ci_error_service import CIErrorService
from baid_server.services.session_service import SessionService
from baid_server.services.message_service import MessageService
from baid_server.services.waitlist_service import WaitlistService
from baid_server.services.user_service import UserService

# Config Imports
from baid_server.config import (
    OAuthConfig, JWTConfig, get_oauth_config, get_jwt_config,
    AgentConfigModel, get_agent_config_model,
    CIErrorServiceConfigModel, get_ci_error_config_model,
)
# Repository Imports (for type hinting in service providers if needed, though mostly resolved by db.dependencies)
from baid_server.db.repositories.message_repository import MessageRepository
from baid_server.db.repositories.session_repository import SessionRepository
from baid_server.db.repositories.waitlist_repository import WaitlistRepository
from baid_server.db.repositories.global_settings_repository import GlobalSettingsRepository

# Utility Imports
from baid_server.utils.response_parser import ResponseParser

# Google Cloud Service Imports
from google.adk.sessions import VertexAiSessionService
from google.cloud.aiplatform_v1.services.reasoning_engine_execution_service import ReasoningEngineExecutionServiceClient


async def get_tenant_service(
    tenant_repo: TenantRepository = Depends(get_tenant_repository_dependency),
    user_repo: UserRepository = Depends(get_user_repository_dependency)
) -> TenantService:
    """
    Dependency provider for TenantService.
    Injects TenantRepository and UserRepository into the TenantService
    using centralized repository providers.
    """
    return TenantService(tenant_repo=tenant_repo, user_repo=user_repo)


async def get_api_key_service(
    user_repo: UserRepository = Depends(get_user_repository_dependency)
) -> ApiKeyService:
    """
    Dependency provider for ApiKeyService.
    Injects UserRepository into the ApiKeyService
    using centralized repository providers.
    """
    return ApiKeyService(user_repo=user_repo)


async def get_auth_service( # MODIFIED to async
    user_repository: UserRepository = Depends(get_user_repository_dependency), # This is async
    oauth_config: OAuthConfig = Depends(get_oauth_config), # This is sync
    jwt_config: JWTConfig = Depends(get_jwt_config) # This is sync
) -> AuthService:
    """
    Dependency provider for AuthService.
    Injects UserRepository, OAuthConfig, and JWTConfig into the AuthService.
    FastAPI handles mixed sync/async dependencies.
    """
    return AuthService(
        user_repository=user_repository, # UserRepository instance is resolved from an async provider
        oauth_config=oauth_config,
        jwt_config=jwt_config
    )

# --- Google Cloud Client Providers ---

def get_reasoning_engine_execution_client(
    config: AgentConfigModel = Depends(get_agent_config_model)
) -> ReasoningEngineExecutionServiceClient:
    """Dependency provider for ReasoningEngineExecutionServiceClient."""
    if not config.LOCATION:
        raise ValueError("Location must be set in AgentConfigModel for ReasoningEngineExecutionServiceClient")
    api_endpoint = f"{config.LOCATION}-aiplatform.googleapis.com"
    return ReasoningEngineExecutionServiceClient(client_options={"api_endpoint": api_endpoint})

def get_vertex_ai_session_service(
    config: AgentConfigModel = Depends(get_agent_config_model)
) -> VertexAiSessionService:
    """Dependency provider for VertexAiSessionService."""
    if not config.PROJECT_ID or not config.LOCATION:
        raise ValueError("PROJECT_ID and LOCATION must be set in AgentConfigModel for VertexAiSessionService")
    return VertexAiSessionService(project=config.PROJECT_ID, location=config.LOCATION)

# --- Utility Providers ---

def get_response_parser() -> ResponseParser:
    """Dependency provider for ResponseParser."""
    return ResponseParser()

# --- Main Service Providers ---

async def get_agent_service(
    config: AgentConfigModel = Depends(get_agent_config_model), # Sync dep
    message_repo: MessageRepository = Depends(get_message_repository_dependency),
    session_repo: SessionRepository = Depends(get_session_repository_dependency),
    response_processor: ResponseParser = Depends(get_response_parser),
    session_service: VertexAiSessionService = Depends(get_vertex_ai_session_service),
    execution_client: ReasoningEngineExecutionServiceClient = Depends(get_reasoning_engine_execution_client),
) -> AgentService:
    """Dependency provider for AgentService."""
    return AgentService(
        config=config,
        message_repository=message_repo,
        session_repository=session_repo,
        response_processor=response_processor,
        session_service=session_service,
        execution_client=execution_client,
    )

async def get_ci_error_service(
    config: CIErrorServiceConfigModel = Depends(get_ci_error_config_model),
    # Assuming CIErrorService uses the same client config as AgentService for now
    execution_client: ReasoningEngineExecutionServiceClient = Depends(get_reasoning_engine_execution_client), # Sync dep
) -> CIErrorService:
    """Dependency provider for CIErrorService."""
    return CIErrorService(
        config=config,
        execution_client=execution_client,
    )

# --- Session Service Provider ---
async def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repository_dependency), # Async dep
) -> SessionService:
    """Dependency provider for SessionService."""
    return SessionService(session_repo=session_repo)

# --- Message Service Provider ---
async def get_message_service(
    message_repo: MessageRepository = Depends(get_message_repository_dependency), # Async dep
) -> MessageService:
    """Dependency provider for MessageService."""
    return MessageService(message_repo=message_repo)

# --- Waitlist Service Provider ---
async def get_waitlist_service(
    waitlist_repo: WaitlistRepository = Depends(get_waitlist_repository_dependency), # Async dep
    auth_service: AuthService = Depends(get_auth_service), # Now async dep
) -> WaitlistService:
    """Dependency provider for WaitlistService."""
    return WaitlistService(waitlist_repo=waitlist_repo, auth_service=auth_service)

# --- User Service Provider ---
async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository_dependency), # Async dep
    global_settings_repo: GlobalSettingsRepository = Depends(get_global_settings_repository_dependency), # Async dep
    message_repo: MessageRepository = Depends(get_message_repository_dependency), # Async dep
) -> UserService:
    """Dependency provider for UserService."""
    return UserService(
        user_repo=user_repo, 
        global_settings_repo=global_settings_repo,
        message_repo=message_repo
    )
