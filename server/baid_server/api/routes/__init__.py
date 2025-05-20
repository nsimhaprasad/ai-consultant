"""API routes package initialization.

This module exports all routers for use in the main application.
"""

from baid_server.api.routes.auth import router as auth
from baid_server.api.routes.agent import router as agent
from baid_server.api.routes.sessions import router as sessions
from baid_server.api.routes.waitlist import router as waitlist
from baid_server.api.routes.api_key import router as api_key
from baid_server.api.routes.auth_api_key import router as auth_api_key
from baid_server.api.routes.ci_error import router as ci_error
from baid_server.api.routes.tenant import router as tenant
from baid_server.api.routes.users import router as users

# Export all routers
__all__ = ['auth', 'agent', 'sessions', 'waitlist', 'api_key', 'auth_api_key', 'ci_error', 'tenant', 'users']
