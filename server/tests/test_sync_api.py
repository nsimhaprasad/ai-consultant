"""Tests for sync API endpoints."""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from baid_server.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_auth_token():
    """Mock JWT token payload."""
    return {
        "sub": "test-user@example.com",
        "name": "Test User",
        "exp": 9999999999  # Far future expiration
    }


@pytest.fixture
def sample_sync_request():
    """Sample sync request data."""
    return {
        "filename": "my-project_20240101_120000.tar.gz",
        "content_type": "application/gzip"
    }


class TestSyncAPI:
    """Test cases for sync API endpoints."""

    @patch('baid_server.api.dependencies.jwt.decode')
    @patch('baid_server.services.sync_service.storage.Client')
    def test_get_signed_url_success(self, mock_storage_client, mock_jwt_decode, client, mock_auth_token, sample_sync_request):
        """Test successful signed URL generation."""
        # Mock JWT decode
        mock_jwt_decode.return_value = mock_auth_token
        
        # Mock GCS client and bucket
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed-url"
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        response = client.post(
            "/api/sync/signed-url",
            json=sample_sync_request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "signed_url" in data
        assert data["signed_url"] == "https://storage.googleapis.com/signed-url"
        assert "expires_at" in data

    @patch('baid_server.api.dependencies.jwt.decode')
    def test_get_signed_url_validation_error(self, mock_jwt_decode, client, mock_auth_token):
        """Test validation error for invalid request."""
        mock_jwt_decode.return_value = mock_auth_token
        
        invalid_request = {
            "filename": "",  # Empty filename
            "content_type": "application/gzip"
        }

        response = client.post(
            "/api/sync/signed-url",
            json=invalid_request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 400
        assert "Filename is required" in response.json()["detail"]

    @patch('baid_server.api.dependencies.jwt.decode')
    @patch('baid_server.services.sync_service.storage.Client')
    def test_get_sync_status_success(self, mock_storage_client, mock_jwt_decode, client, mock_auth_token):
        """Test successful sync status retrieval."""
        mock_jwt_decode.return_value = mock_auth_token
        
        # Mock bucket info
        mock_bucket = Mock()
        mock_bucket.location = "us-central1"
        mock_bucket.storage_class = "STANDARD"
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        response = client.get(
            "/api/sync/status",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["user_id"] == "test-user@example.com"
        assert "storage" in data
        assert "timestamp" in data

    def test_unauthorized_access(self, client, sample_sync_request):
        """Test unauthorized access without token."""
        response = client.post("/api/sync/signed-url", json=sample_sync_request)
        assert response.status_code == 403  # FastAPI returns 403 for missing bearer token

    @patch('baid_server.api.dependencies.jwt.decode')
    def test_invalid_token(self, mock_jwt_decode, client, sample_sync_request):
        """Test invalid JWT token."""
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        response = client.post(
            "/api/sync/signed-url",
            json=sample_sync_request,
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401