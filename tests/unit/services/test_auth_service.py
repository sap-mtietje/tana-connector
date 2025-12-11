"""Unit tests for auth_service module"""

import pytest
from unittest.mock import MagicMock, patch
from azure.identity import (
    InteractiveBrowserCredential,
    AuthenticationRecord,
)

from app.services.auth_service import AuthService, auth_service


@pytest.mark.unit
class TestAuthService:
    """Tests for AuthService class"""

    def setup_method(self):
        """Reset service state before each test"""
        self.service = AuthService()

    def test_service_initialization(self):
        """Should initialize with no credential"""
        service = AuthService()
        assert service.credential is None
        assert service._auth_record is None

    @patch("app.services.auth_service.InteractiveBrowserCredential")
    @patch.object(AuthService, "_load_auth_record")
    async def test_get_credential_with_existing_record(
        self, mock_load_record, mock_credential_class
    ):
        """Should create credential with existing auth record"""
        # Setup mocks
        mock_record = MagicMock(spec=AuthenticationRecord)
        mock_load_record.return_value = mock_record

        mock_credential = MagicMock(spec=InteractiveBrowserCredential)
        mock_credential_class.return_value = mock_credential

        # Call get_credential
        credential = await self.service.get_credential()

        # Verify auth record was loaded
        mock_load_record.assert_called_once()

        # Verify credential was created with auth record
        mock_credential_class.assert_called_once()
        call_kwargs = mock_credential_class.call_args[1]
        assert call_kwargs["authentication_record"] == mock_record

        # Verify no interactive authentication was performed
        assert credential == mock_credential

    @patch("app.services.auth_service.InteractiveBrowserCredential")
    @patch.object(AuthService, "_load_auth_record")
    @patch.object(AuthService, "_authenticate")
    async def test_get_credential_without_existing_record(
        self, mock_authenticate, mock_load_record, mock_credential_class
    ):
        """Should perform interactive auth when no record exists"""
        # Setup mocks
        mock_load_record.return_value = None
        mock_authenticate.return_value = None

        mock_credential = MagicMock(spec=InteractiveBrowserCredential)
        mock_credential_class.return_value = mock_credential

        # Call get_credential
        credential = await self.service.get_credential()

        # Verify auth record was loaded
        mock_load_record.assert_called_once()

        # Verify interactive authentication was performed
        mock_authenticate.assert_called_once()

        # Verify credential was created
        assert credential == mock_credential

    @patch("app.services.auth_service.InteractiveBrowserCredential")
    @patch.object(AuthService, "_load_auth_record")
    async def test_get_credential_returns_cached(
        self, mock_load_record, mock_credential_class
    ):
        """Should return cached credential on subsequent calls"""
        # Setup mocks
        mock_record = MagicMock(spec=AuthenticationRecord)
        mock_load_record.return_value = mock_record

        mock_credential = MagicMock(spec=InteractiveBrowserCredential)
        mock_credential_class.return_value = mock_credential

        # First call
        credential1 = await self.service.get_credential()

        # Second call
        credential2 = await self.service.get_credential()

        # Verify credential was only created once
        assert mock_credential_class.call_count == 1

        # Verify same credential is returned
        assert credential1 is credential2

    @patch("app.services.auth_service.asyncio.to_thread")
    @patch.object(AuthService, "_save_auth_record")
    async def test_authenticate_performs_interactive_auth(
        self, mock_save_record, mock_to_thread
    ):
        """Should perform interactive authentication and save record"""
        # Setup mock credential
        mock_credential = MagicMock(spec=InteractiveBrowserCredential)
        mock_record = MagicMock(spec=AuthenticationRecord)

        mock_to_thread.return_value = mock_record

        self.service.credential = mock_credential

        # Call _authenticate
        await self.service._authenticate()

        # Verify authentication was performed
        mock_to_thread.assert_called_once()

        # Verify record was saved
        mock_save_record.assert_called_once_with(mock_record)

    async def test_authenticate_without_credential_raises_error(self):
        """Should raise AuthenticationError if credential not initialized"""
        from app.exceptions import AuthenticationError

        self.service.credential = None

        with pytest.raises(AuthenticationError, match="Credential not initialized"):
            await self.service._authenticate()

    @patch("app.services.auth_service.AUTH_RECORD_PATH")
    @patch("app.services.auth_service.AuthenticationRecord")
    def test_load_auth_record_success(self, mock_record_class, mock_path):
        """Should load and deserialize auth record from file"""
        # Setup mocks
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = '{"some": "data"}'

        mock_record = MagicMock(spec=AuthenticationRecord)
        mock_record_class.deserialize.return_value = mock_record

        # Call _load_auth_record
        result = self.service._load_auth_record()

        # Verify file was read
        mock_path.exists.assert_called_once()
        mock_path.read_text.assert_called_once_with(encoding="utf-8")

        # Verify record was deserialized
        mock_record_class.deserialize.assert_called_once_with('{"some": "data"}')
        assert result == mock_record

    @patch("app.services.auth_service.AUTH_RECORD_PATH")
    def test_load_auth_record_file_not_exists(self, mock_path):
        """Should return None when auth record file doesn't exist"""
        mock_path.exists.return_value = False

        result = self.service._load_auth_record()

        assert result is None

    @patch("app.services.auth_service.AUTH_RECORD_PATH")
    @patch("app.services.auth_service.AuthenticationRecord")
    def test_load_auth_record_handles_error(self, mock_record_class, mock_path):
        """Should return None and print warning on load error"""
        # Setup mocks to raise an error
        mock_path.exists.return_value = True
        mock_record_class.deserialize.side_effect = Exception("Parse error")

        result = self.service._load_auth_record()

        assert result is None

    @patch("app.services.auth_service.AUTH_RECORD_PATH")
    def test_save_auth_record_success(self, mock_path):
        """Should serialize and save auth record to file"""
        # Setup mock record
        mock_record = MagicMock(spec=AuthenticationRecord)
        mock_record.serialize.return_value = '{"some": "data"}'

        # Call _save_auth_record
        self.service._save_auth_record(mock_record)

        # Verify record was serialized
        mock_record.serialize.assert_called_once()

        # Verify file was written
        mock_path.write_text.assert_called_once_with(
            '{"some": "data"}', encoding="utf-8"
        )

    @patch("app.services.auth_service.AUTH_RECORD_PATH")
    def test_save_auth_record_handles_error(self, mock_path):
        """Should handle and print warning on save error"""
        # Setup mocks to raise an error
        mock_record = MagicMock(spec=AuthenticationRecord)
        mock_record.serialize.return_value = '{"some": "data"}'
        mock_path.write_text.side_effect = Exception("Write error")

        # Call _save_auth_record (should not raise)
        self.service._save_auth_record(mock_record)

        # Verify error was caught (no exception raised)
        mock_path.write_text.assert_called_once()


@pytest.mark.unit
class TestAuthServiceSingleton:
    """Tests for the global auth_service instance"""

    def test_global_instance_exists(self):
        """Should have a global auth_service instance"""
        assert auth_service is not None
        assert isinstance(auth_service, AuthService)

    def test_global_instance_is_singleton(self):
        """Should use the same instance across imports"""
        from app.services.auth_service import auth_service as imported_service

        assert auth_service is imported_service


@pytest.mark.unit
class TestAuthServiceConfiguration:
    """Tests for AuthService configuration"""

    @patch("app.services.auth_service.InteractiveBrowserCredential")
    @patch("app.services.auth_service.CLIENT_ID", "test-client-id")
    @patch("app.services.auth_service.TENANT_ID", "test-tenant-id")
    @patch.object(AuthService, "_load_auth_record")
    async def test_credential_created_with_correct_config(
        self, mock_load_record, mock_credential_class
    ):
        """Should create credential with correct configuration"""
        service = AuthService()
        mock_load_record.return_value = None

        with patch.object(AuthService, "_authenticate"):
            await service.get_credential()

        # Verify credential was created with correct config
        mock_credential_class.assert_called_once()
        call_kwargs = mock_credential_class.call_args[1]

        assert call_kwargs["client_id"] == "test-client-id"
        assert call_kwargs["tenant_id"] == "test-tenant-id"
        assert "cache_persistence_options" in call_kwargs
