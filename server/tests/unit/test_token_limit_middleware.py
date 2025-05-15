"""Unit tests for the token limit middleware."""
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from baid_server.api.middleware.token_limit_middleware import TokenLimitMiddleware


class TestTokenLimitMiddleware:
    """Test cases for the TokenLimitMiddleware class."""

    @pytest.fixture
    def middleware(self):
        """Create a TokenLimitMiddleware instance for testing."""
        mock_app = MagicMock()
        middleware = TokenLimitMiddleware(app=mock_app)
        # Mock the _check_user_limits method to avoid database calls
        middleware._check_user_limits = AsyncMock()
        return middleware

    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/consult"
        request.state = MagicMock()
        request.state.user = {"sub": "test_user_id"}
        return request

    @pytest.fixture
    def mock_call_next(self):
        """Create a mock call_next function for testing."""
        async def call_next_mock(request):
            return JSONResponse(content={"status": "success"})
        return call_next_mock

    @pytest.mark.asyncio
    async def test_allowed_request(self, middleware, mock_request, mock_call_next):
        """Test that a request is allowed when user is not restricted and under token limit."""
        # Configure the mock to return values indicating user is not restricted and under limit
        middleware._check_user_limits.return_value = (False, 5000, 10000)  # (is_restricted, token_usage, token_limit)
        
        # Execute middleware
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify response
        assert response.status_code == 200
        middleware._check_user_limits.assert_called_once_with("test_user_id")
        assert "token_info" in mock_request.state.__dict__
        assert mock_request.state.token_info["usage"] == 5000
        assert mock_request.state.token_info["limit"] == 10000

    @pytest.mark.asyncio
    async def test_restricted_user(self, middleware, mock_request, mock_call_next):
        """Test that a request is rejected when user is restricted."""
        # Configure the mock to return values indicating user is restricted
        middleware._check_user_limits.return_value = (True, 5000, 10000)  # (is_restricted, token_usage, token_limit)
        
        # Execute middleware and expect exception
        with pytest.raises(HTTPException) as excinfo:
            await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify exception
        middleware._check_user_limits.assert_called_once_with("test_user_id")
        assert excinfo.value.status_code == 403
        assert "restricted" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_token_limit_exceeded(self, middleware, mock_request, mock_call_next):
        """Test that a request is rejected when user exceeds token limit."""
        # Configure the mock to return values indicating user is over their token limit
        middleware._check_user_limits.return_value = (False, 12000, 10000)  # (is_restricted, token_usage, token_limit)
        
        # Execute middleware and expect exception
        with pytest.raises(HTTPException) as excinfo:
            await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify exception
        middleware._check_user_limits.assert_called_once_with("test_user_id")
        assert excinfo.value.status_code == 429
        assert "token limit" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_non_consult_endpoint(self, middleware, mock_call_next):
        """Test that middleware doesn't check token limits for non-consult endpoints."""
        # Create request for a different endpoint
        request = MagicMock(spec=Request)
        request.url.path = "/api/some-other-endpoint"
        request.state = MagicMock()
        request.state.user = {"sub": "test_user_id"}
        
        # Execute middleware
        response = await middleware.dispatch(request, mock_call_next)
        
        # Verify response and that token check was not called
        assert response.status_code == 200
        middleware._check_user_limits.assert_not_called()

