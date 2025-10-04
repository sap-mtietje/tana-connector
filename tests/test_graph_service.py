"""Unit tests for graph_service module"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from msgraph import GraphServiceClient

from app.services.graph_service import GraphService, graph_service


@pytest.mark.unit
class TestGraphService:
    """Tests for GraphService class"""
    
    def setup_method(self):
        """Reset service state before each test"""
        # Create a fresh instance for testing
        self.service = GraphService()
    
    @patch("app.services.graph_service.auth_service")
    async def test_get_client_creates_new_client(self, mock_auth_service):
        """Should create a new Graph client on first call"""
        # Setup mock credential
        mock_credential = MagicMock()
        mock_auth_service.get_credential = AsyncMock(return_value=mock_credential)
        
        # Call get_client
        client = await self.service.get_client()
        
        # Verify credential was fetched
        mock_auth_service.get_credential.assert_called_once()
        
        # Verify client was created
        assert client is not None
        assert isinstance(client, GraphServiceClient)
        assert self.service.client is not None
    
    @patch("app.services.graph_service.auth_service")
    async def test_get_client_returns_cached_client(self, mock_auth_service):
        """Should return cached client on subsequent calls"""
        # Setup mock credential
        mock_credential = MagicMock()
        mock_auth_service.get_credential = AsyncMock(return_value=mock_credential)
        
        # First call
        client1 = await self.service.get_client()
        
        # Second call
        client2 = await self.service.get_client()
        
        # Verify credential was only fetched once
        assert mock_auth_service.get_credential.call_count == 1
        
        # Verify same client instance is returned
        assert client1 is client2
    
    @patch("app.services.graph_service.auth_service")
    async def test_get_user_info(self, mock_auth_service):
        """Should fetch user info using Graph client"""
        # Setup mock credential and client
        mock_credential = MagicMock()
        mock_auth_service.get_credential = AsyncMock(return_value=mock_credential)
        
        # Create a mock user object
        mock_user = MagicMock()
        mock_user.display_name = "John Doe"
        mock_user.mail = "john@example.com"
        
        # Mock the Graph client's me.get() method
        with patch.object(GraphServiceClient, '__init__', return_value=None):
            with patch('msgraph.GraphServiceClient') as mock_graph_client_class:
                mock_client_instance = MagicMock()
                mock_client_instance.me.get = AsyncMock(return_value=mock_user)
                mock_graph_client_class.return_value = mock_client_instance
                
                # Manually set the client
                self.service.client = mock_client_instance
                
                # Call get_user_info
                user = await self.service.get_user_info()
                
                # Verify user info was fetched
                assert user.display_name == "John Doe"
                assert user.mail == "john@example.com"
                mock_client_instance.me.get.assert_called_once()
    
    def test_service_initialization(self):
        """Should initialize with no client"""
        service = GraphService()
        assert service.client is None
    
    @patch("app.services.graph_service.auth_service")
    async def test_get_client_with_auth_failure(self, mock_auth_service):
        """Should propagate authentication errors"""
        # Setup mock to raise an error
        mock_auth_service.get_credential = AsyncMock(
            side_effect=RuntimeError("Authentication failed")
        )
        
        # Call get_client and expect error
        with pytest.raises(RuntimeError, match="Authentication failed"):
            await self.service.get_client()


@pytest.mark.unit
class TestGraphServiceSingleton:
    """Tests for the global graph_service instance"""
    
    def test_global_instance_exists(self):
        """Should have a global graph_service instance"""
        assert graph_service is not None
        assert isinstance(graph_service, GraphService)
    
    def test_global_instance_is_singleton(self):
        """Should use the same instance across imports"""
        from app.services.graph_service import graph_service as imported_service
        assert graph_service is imported_service
