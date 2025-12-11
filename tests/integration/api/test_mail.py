"""
Integration tests for mail router endpoints.

Tests cover:
- GET /me/mailFolders/{folder_id}/messages/delta
- POST /me/mailFolders/{folder_id}/messages/delta/render
- DELETE /me/mailFolders/{folder_id}/messages/delta/cache
- GET /me/mailFolders/{folder_id}/messages/delta/cache
- POST /me/messages (create draft)
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


# Test message factory
def make_ms_graph_message(**overrides):
    """Create a test message in MS Graph format"""
    base = {
        "id": "msg-123",
        "subject": "Test Subject",
        "bodyPreview": "This is a preview of the email body",
        "body": {"contentType": "html", "content": "<p>Email content</p>"},
        "from": {"emailAddress": {"name": "John Doe", "address": "john@example.com"}},
        "toRecipients": [
            {"emailAddress": {"name": "Jane Smith", "address": "jane@example.com"}}
        ],
        "receivedDateTime": "2025-10-05T10:00:00Z",
        "sentDateTime": "2025-10-05T09:59:00Z",
        "isRead": False,
        "isDraft": False,
        "hasAttachments": False,
        "importance": "normal",
        "categories": [],
        "webLink": "https://outlook.office.com/mail/123",
    }
    base.update(overrides)
    return base


class TestMailDeltaGet:
    """Tests for GET /me/mailFolders/{folder_id}/messages/delta"""

    def test_get_messages_delta_json(self, client, mock_mail_service):
        """Test GET returns JSON by default"""
        mock_mail_service.return_value = {
            "value": [make_ms_graph_message()],
            "@odata.count": 1,
            "_cached": False,
            "_isInitialSync": True,
        }

        response = client.get("/me/mailFolders/inbox/messages/delta")

        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 1
        assert data["value"][0]["subject"] == "Test Subject"

    def test_get_messages_delta_tana_format(self, client, mock_mail_service):
        """Test GET with _format=tana returns Tana Paste"""
        mock_mail_service.return_value = {
            "value": [make_ms_graph_message(subject="Important Email")],
            "@odata.count": 1,
            "_cached": False,
            "_isInitialSync": True,
        }

        response = client.get("/me/mailFolders/inbox/messages/delta?_format=tana")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "%%tana%%" in response.text
        assert "Important Email" in response.text

    def test_get_messages_delta_with_post_filter(self, client, mock_mail_service):
        """Test GET with _filter applies post-fetch filtering"""
        mock_mail_service.return_value = {
            "value": [
                make_ms_graph_message(id="1", categories=["Work"]),
                make_ms_graph_message(id="2", categories=["Personal"]),
            ],
            "@odata.count": 2,
            "_cached": False,
            "_isInitialSync": True,
        }

        response = client.get(
            "/me/mailFolders/inbox/messages/delta?_filter=categories:Work"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["_filtered"] is True
        assert data["_filteredCount"] == 1
        assert data["_originalCount"] == 2

    def test_get_messages_delta_with_select(self, client, mock_mail_service):
        """Test GET with select parameter"""
        mock_mail_service.return_value = {
            "value": [make_ms_graph_message()],
            "@odata.count": 1,
            "_cached": False,
            "_isInitialSync": True,
        }

        response = client.get(
            "/me/mailFolders/inbox/messages/delta?select=subject,from"
        )

        assert response.status_code == 200
        # Verify select was passed to service
        call_kwargs = mock_mail_service.call_args.kwargs
        assert call_kwargs["select"] == ["subject", "from"]

    def test_get_messages_delta_well_known_folder(self, client, mock_mail_service):
        """Test GET with well-known folder names"""
        mock_mail_service.return_value = {
            "value": [],
            "@odata.count": 0,
            "_cached": False,
            "_isInitialSync": True,
        }

        # Test various well-known folder names
        for folder in ["inbox", "sent", "drafts", "deleted", "junk"]:
            response = client.get(f"/me/mailFolders/{folder}/messages/delta")
            assert response.status_code == 200

    def test_get_messages_delta_error_handling(self, client, mock_mail_service):
        """Test error handling when service fails"""
        mock_mail_service.side_effect = Exception("API Error")

        response = client.get("/me/mailFolders/inbox/messages/delta")

        assert response.status_code == 502
        assert "Failed to fetch messages delta" in response.json()["message"]


class TestMailDeltaPost:
    """Tests for POST /me/mailFolders/{folder_id}/messages/delta/render"""

    def test_post_with_template(self, client, mock_mail_service):
        """Test POST with custom template"""
        mock_mail_service.return_value = {
            "value": [make_ms_graph_message(subject="Test Email")],
            "@odata.count": 1,
            "_cached": False,
            "_isInitialSync": True,
        }

        template = "{% for msg in messages %}{{ msg.subject }}{% endfor %}"

        response = client.post(
            "/me/mailFolders/inbox/messages/delta/render",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        assert "Test Email" in response.text

    def test_post_with_tana_template(self, client, mock_mail_service):
        """Test POST with Tana Paste template"""
        mock_mail_service.return_value = {
            "value": [
                make_ms_graph_message(subject="Email 1"),
                make_ms_graph_message(subject="Email 2"),
            ],
            "@odata.count": 2,
            "_cached": False,
            "_isInitialSync": True,
        }

        template = """%%tana%%
{% for msg in messages %}
- {{ msg.subject }} #email
{% endfor %}"""

        response = client.post(
            "/me/mailFolders/inbox/messages/delta/render",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        assert "%%tana%%" in response.text
        assert "Email 1" in response.text
        assert "Email 2" in response.text

    def test_post_with_filter(self, client, mock_mail_service):
        """Test POST with post-fetch filter"""
        mock_mail_service.return_value = {
            "value": [
                make_ms_graph_message(
                    id="1", subject="Work Email", categories=["Work"]
                ),
                make_ms_graph_message(
                    id="2", subject="Personal Email", categories=["Personal"]
                ),
            ],
            "@odata.count": 2,
            "_cached": False,
            "_isInitialSync": True,
        }

        template = "{{ count }} messages"

        response = client.post(
            "/me/mailFolders/inbox/messages/delta/render?_filter=categories:Work",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        assert "1 messages" in response.text

    def test_post_empty_template_returns_error(self, client, mock_mail_service):
        """Test POST with empty template returns error"""
        response = client.post(
            "/me/mailFolders/inbox/messages/delta/render",
            content="",
            headers={"Content-Type": "text/plain"},
        )

        # FastAPI returns 422 for validation errors, 400 for explicit HTTPException
        assert response.status_code in (400, 422)

    def test_post_invalid_template_returns_400(self, client, mock_mail_service):
        """Test POST with invalid Jinja2 template returns 400"""
        mock_mail_service.return_value = {
            "value": [],
            "@odata.count": 0,
            "_cached": False,
            "_isInitialSync": True,
        }

        template = "{% for msg in messages %}"  # Missing endfor

        response = client.post(
            "/me/mailFolders/inbox/messages/delta/render",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 400

    def test_post_template_context_variables(self, client, mock_mail_service):
        """Test that template receives correct context variables"""
        mock_mail_service.return_value = {
            "value": [make_ms_graph_message()],
            "@odata.count": 1,
            "_cached": True,
            "_isInitialSync": False,
        }

        template = (
            "count={{ count }}, cached={{ cached }}, initial={{ is_initial_sync }}"
        )

        response = client.post(
            "/me/mailFolders/inbox/messages/delta/render",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        assert "count=1" in response.text
        assert "cached=True" in response.text
        assert "initial=False" in response.text


class TestMailDeltaCache:
    """Tests for delta cache management endpoints"""

    def test_delete_cache(self, client, mock_delta_cache_service):
        """Test DELETE clears cache"""
        mock_delta_cache_service.clear_token.return_value = True

        response = client.delete("/me/mailFolders/inbox/messages/delta/cache")

        assert response.status_code == 200
        data = response.json()
        assert data["cleared"] is True
        assert "Delta cache cleared" in data["message"]

    def test_delete_cache_not_exists(self, client, mock_delta_cache_service):
        """Test DELETE when no cache exists"""
        mock_delta_cache_service.clear_token.return_value = False

        response = client.delete("/me/mailFolders/inbox/messages/delta/cache")

        assert response.status_code == 200
        data = response.json()
        assert data["cleared"] is False
        assert "No cache existed" in data["message"]

    def test_get_cache_info_exists(self, client, mock_delta_cache_service):
        """Test GET cache info when cache exists"""
        mock_delta_cache_service.get_cache_info.return_value = {
            "delta_link": "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages/delta?$deltatoken=abc123",
            "updated_at": "2025-10-05T10:00:00Z",
        }

        response = client.get("/me/mailFolders/inbox/messages/delta/cache")

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert "updated_at" in data
        assert "delta_link_preview" in data

    def test_get_cache_info_not_exists(self, client, mock_delta_cache_service):
        """Test GET cache info when no cache exists"""
        mock_delta_cache_service.get_cache_info.return_value = None

        response = client.get("/me/mailFolders/inbox/messages/delta/cache")

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is False
        assert "No delta token cached" in data["message"]


class TestCreateDraft:
    """Tests for POST /me/messages (create draft)"""

    def test_create_draft_basic(self, client, mock_mail_service_create_draft):
        """Test creating a basic draft"""
        mock_mail_service_create_draft.return_value = make_ms_graph_message(
            id="draft-123",
            subject="Test Draft",
            isDraft=True,
        )

        response = client.post(
            "/me/messages",
            json={
                "subject": "Test Draft",
                "body": {"contentType": "HTML", "content": "<p>Draft content</p>"},
                "toRecipients": [{"address": "recipient@example.com"}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Test Draft"

    def test_create_draft_with_all_fields(self, client, mock_mail_service_create_draft):
        """Test creating a draft with all optional fields"""
        mock_mail_service_create_draft.return_value = make_ms_graph_message(
            id="draft-456",
            subject="Full Draft",
            isDraft=True,
            importance="high",
        )

        response = client.post(
            "/me/messages",
            json={
                "subject": "Full Draft",
                "body": {"contentType": "Text", "content": "Plain text content"},
                "toRecipients": [{"address": "to@example.com", "name": "To Person"}],
                "ccRecipients": [{"address": "cc@example.com", "name": "CC Person"}],
                "bccRecipients": [{"address": "bcc@example.com"}],
                "importance": "high",
            },
        )

        assert response.status_code == 200
        # Verify all recipients were passed
        call_kwargs = mock_mail_service_create_draft.call_args.kwargs
        assert call_kwargs["to_recipients"] is not None
        assert call_kwargs["cc_recipients"] is not None
        assert call_kwargs["bcc_recipients"] is not None
        assert call_kwargs["importance"] == "high"

    def test_create_draft_error_handling(self, client, mock_mail_service_create_draft):
        """Test error handling when draft creation fails"""
        mock_mail_service_create_draft.side_effect = Exception("API Error")

        response = client.post(
            "/me/messages",
            json={
                "subject": "Test",
                "body": {"contentType": "HTML", "content": "<p>Test</p>"},
            },
        )

        assert response.status_code == 502
        assert "Failed to create draft" in response.json()["message"]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_mail_service():
    """Mock MailService using FastAPI dependency override"""
    os.environ["CLIENT_ID"] = "test-client-id"
    os.environ["TENANT_ID"] = "test-tenant-id"

    from app.main import app
    from app.dependencies import get_mail_service, reset_singletons
    from app.services.mail_service import MailService

    # Create a real service with mock dependencies for format_as_tana
    mock_graph = MagicMock()
    mock_delta_cache = MagicMock()
    real_service = MailService(
        graph_service=mock_graph,
        delta_cache_service=mock_delta_cache,
    )

    # Create a mock service
    mock_service = MagicMock(spec=MailService)
    mock_service.get_messages_delta = AsyncMock()
    mock_service.format_as_tana = real_service.format_as_tana

    # Override the dependency
    app.dependency_overrides[get_mail_service] = lambda: mock_service

    yield mock_service.get_messages_delta

    # Clean up
    app.dependency_overrides.clear()
    reset_singletons()


@pytest.fixture
def mock_mail_service_create_draft():
    """Mock MailService.create_draft using FastAPI dependency override"""
    os.environ["CLIENT_ID"] = "test-client-id"
    os.environ["TENANT_ID"] = "test-tenant-id"

    from app.main import app
    from app.dependencies import get_mail_service, reset_singletons
    from app.services.mail_service import MailService

    # Create a mock service
    mock_service = MagicMock(spec=MailService)
    mock_service.create_draft = AsyncMock()

    # Override the dependency
    app.dependency_overrides[get_mail_service] = lambda: mock_service

    yield mock_service.create_draft

    # Clean up
    app.dependency_overrides.clear()
    reset_singletons()


@pytest.fixture
def mock_delta_cache_service():
    """Mock DeltaCacheService using FastAPI dependency override"""
    os.environ["CLIENT_ID"] = "test-client-id"
    os.environ["TENANT_ID"] = "test-tenant-id"

    from app.main import app
    from app.dependencies import get_delta_cache_service, reset_singletons

    # Create a mock service
    mock_service = MagicMock()

    # Override the dependency
    app.dependency_overrides[get_delta_cache_service] = lambda: mock_service

    yield mock_service

    # Clean up
    app.dependency_overrides.clear()
    reset_singletons()


@pytest.fixture
def client():
    """FastAPI test client"""
    os.environ["CLIENT_ID"] = "test-client-id"
    os.environ["TENANT_ID"] = "test-tenant-id"

    from app.main import app

    return TestClient(app)
