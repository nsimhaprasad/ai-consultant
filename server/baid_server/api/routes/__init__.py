"""API routes package initialization.

This module exports all routers for use in the main application.
"""

from baid_server.api.routes.auth import router as auth
from baid_server.api.routes.agent import router as agent
from baid_server.api.routes.sessions import router as sessions
from baid_server.api.routes.waitlist import router as waitlist

# Export all routers
__all__ = ['auth', 'agent', 'sessions', 'waitlist']
