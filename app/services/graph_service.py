"""Microsoft Graph API service."""

from __future__ import annotations

from typing import Optional

from msgraph import GraphServiceClient

from app.config import GRAPH_SCOPES
from app.logging import get_logger
from app.services.auth_service import AuthService

logger = get_logger(__name__)


class GraphService:
    """Handles Microsoft Graph API interactions.

    Args:
        auth_service: AuthService instance for authentication (required).
    """

    def __init__(self, auth_service: AuthService) -> None:
        self._auth_service = auth_service
        self._client: Optional[GraphServiceClient] = None

    async def get_client(self) -> GraphServiceClient:
        """Get or create a Graph API client.

        Returns:
            GraphServiceClient: Authenticated Microsoft Graph client.
        """
        if self._client is not None:
            return self._client

        # Get authenticated credential
        credential = await self._auth_service.get_credential()

        # Create Graph client
        self._client = GraphServiceClient(credentials=credential, scopes=GRAPH_SCOPES)
        logger.debug("Graph client initialized")

        return self._client

    async def get_user_info(self):
        """Get current user information.

        Returns:
            User object with display name, email, etc.
        """
        client = await self.get_client()
        return await client.me.get()
