"""MSAL authentication service for Microsoft Graph API"""

import asyncio
from typing import Optional
from azure.identity import (
    InteractiveBrowserCredential,
    TokenCachePersistenceOptions,
    AuthenticationRecord,
)

from app.config import CLIENT_ID, TENANT_ID, GRAPH_SCOPES, AUTH_RECORD_PATH


class AuthService:
    """Handles Microsoft authentication and token management"""
    
    def __init__(self):
        self.credential: Optional[InteractiveBrowserCredential] = None
        self._auth_record: Optional[AuthenticationRecord] = None
    
    async def get_credential(self) -> InteractiveBrowserCredential:
        """
        Get or create an authenticated credential
        
        Returns:
            InteractiveBrowserCredential: Authenticated credential for Graph API
        """
        if self.credential is not None:
            return self.credential
        
        # Setup persistent token cache
        cache_opts = TokenCachePersistenceOptions(
            name="tana-connector",
            allow_unencrypted_storage=False
        )
        
        # Try to load existing authentication record
        auth_record = self._load_auth_record()
        
        # Create credential
        self.credential = InteractiveBrowserCredential(
            client_id=CLIENT_ID,
            tenant_id=TENANT_ID,
            cache_persistence_options=cache_opts,
            authentication_record=auth_record,
        )
        
        # If no auth record exists, authenticate interactively
        if auth_record is None:
            await self._authenticate()
        
        return self.credential
    
    async def _authenticate(self) -> None:
        """Perform interactive authentication and save the record"""
        if self.credential is None:
            raise RuntimeError("Credential not initialized")
        
        print("🔐 First-time authentication required...")
        print("📝 Please complete the authentication in your browser")
        
        # Perform interactive authentication
        new_record = await asyncio.to_thread(
            self.credential.authenticate,
            scopes=GRAPH_SCOPES
        )
        
        # Save the authentication record
        self._save_auth_record(new_record)
        print("✅ Authentication successful and saved!")
    
    def _load_auth_record(self) -> Optional[AuthenticationRecord]:
        """Load authentication record from disk"""
        if not AUTH_RECORD_PATH.exists():
            return None
        
        try:
            record_data = AUTH_RECORD_PATH.read_text(encoding="utf-8")
            return AuthenticationRecord.deserialize(record_data)
        except Exception as e:
            print(f"⚠️  Failed to load auth record: {e}")
            return None
    
    def _save_auth_record(self, record: AuthenticationRecord) -> None:
        """Save authentication record to disk"""
        try:
            AUTH_RECORD_PATH.write_text(record.serialize(), encoding="utf-8")
        except Exception as e:
            print(f"⚠️  Failed to save auth record: {e}")


# Global auth service instance
auth_service = AuthService()


