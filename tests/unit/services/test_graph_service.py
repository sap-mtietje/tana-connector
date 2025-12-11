"""Unit tests for graph_service module"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from msgraph import GraphServiceClient

from app.services.graph_service import GraphService


def _create_graph_service() -> GraphService:
    """Create a GraphService with a mock AuthService."""
    mock_auth_service = MagicMock()
    mock_auth_service.get_credential = AsyncMock()
    return GraphService(auth_service=mock_auth_service)


@pytest.mark.unit
class TestGraphService:
    """Tests for GraphService class"""

    def setup_method(self):
        """Reset service state before each test"""
        # Create a fresh instance for testing with mock auth service
        self.mock_auth_service = MagicMock()
        self.service = GraphService(auth_service=self.mock_auth_service)

    async def test_get_client_creates_new_client(self):
        """Should create a new Graph client on first call"""
        # Setup mock credential
        mock_credential = MagicMock()
        self.mock_auth_service.get_credential = AsyncMock(return_value=mock_credential)

        # Call get_client
        client = await self.service.get_client()

        # Verify credential was fetched
        self.mock_auth_service.get_credential.assert_called_once()

        # Verify client was created
        assert client is not None
        assert isinstance(client, GraphServiceClient)
        assert self.service._client is not None

    async def test_get_client_returns_cached_client(self):
        """Should return cached client on subsequent calls"""
        # Setup mock credential
        mock_credential = MagicMock()
        self.mock_auth_service.get_credential = AsyncMock(return_value=mock_credential)

        # First call
        client1 = await self.service.get_client()

        # Second call
        client2 = await self.service.get_client()

        # Verify credential was only fetched once
        assert self.mock_auth_service.get_credential.call_count == 1

        # Verify same client instance is returned
        assert client1 is client2

    async def test_get_user_info(self):
        """Should fetch user info using Graph client"""
        # Setup mock credential
        mock_credential = MagicMock()
        self.mock_auth_service.get_credential = AsyncMock(return_value=mock_credential)

        # Create a mock user object
        mock_user = MagicMock()
        mock_user.display_name = "John Doe"
        mock_user.mail = "john@example.com"

        # Mock the Graph client's me.get() method
        mock_client_instance = MagicMock()
        mock_client_instance.me.get = AsyncMock(return_value=mock_user)

        # Manually set the client
        self.service._client = mock_client_instance

        # Call get_user_info
        user = await self.service.get_user_info()

        # Verify user info was fetched
        assert user.display_name == "John Doe"
        assert user.mail == "john@example.com"
        mock_client_instance.me.get.assert_called_once()

    def test_service_initialization(self):
        """Should initialize with no client"""
        mock_auth = MagicMock()
        service = GraphService(auth_service=mock_auth)
        assert service._client is None

    async def test_get_client_with_auth_failure(self):
        """Should propagate authentication errors"""
        # Setup mock to raise an error
        self.mock_auth_service.get_credential = AsyncMock(
            side_effect=RuntimeError("Authentication failed")
        )

        # Call get_client and expect error
        with pytest.raises(RuntimeError, match="Authentication failed"):
            await self.service.get_client()
