"""Microsoft Graph API service"""

from typing import Optional
from msgraph import GraphServiceClient

from app.config import GRAPH_SCOPES
from app.services.auth_service import auth_service


class GraphService:
    """Handles Microsoft Graph API interactions"""

    def __init__(self):
        self.client: Optional[GraphServiceClient] = None

    async def get_client(self) -> GraphServiceClient:
        """
        Get or create a Graph API client

        Returns:
            GraphServiceClient: Authenticated Microsoft Graph client
        """
        if self.client is not None:
            return self.client

        # Get authenticated credential
        credential = await auth_service.get_credential()

        # Create Graph client
        self.client = GraphServiceClient(credentials=credential, scopes=GRAPH_SCOPES)

        return self.client

    async def get_user_info(self):
        """
        Get current user information

        Returns:
            User object with display name, email, etc.
        """
        client = await self.get_client()
        return await client.me.get()


# Global graph service instance
graph_service = GraphService()
