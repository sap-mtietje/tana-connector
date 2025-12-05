"""Unit tests for MailService"""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from app.services.mail_service import MailService


class TestBuildRecipients:
    """Tests for MailService._build_recipients method"""

    def setup_method(self):
        self.service = MailService()

    def test_single_recipient_with_name(self):
        """Test building single recipient with name"""
        recipients = [{"address": "john@example.com", "name": "John Doe"}]

        result = self.service._build_recipients(recipients)

        assert len(result) == 1
        assert result[0].email_address.address == "john@example.com"
        assert result[0].email_address.name == "John Doe"

    def test_single_recipient_without_name(self):
        """Test building single recipient without name"""
        recipients = [{"address": "john@example.com"}]

        result = self.service._build_recipients(recipients)

        assert len(result) == 1
        assert result[0].email_address.address == "john@example.com"
        assert result[0].email_address.name is None

    def test_multiple_recipients(self):
        """Test building multiple recipients"""
        recipients = [
            {"address": "john@example.com", "name": "John Doe"},
            {"address": "jane@example.com", "name": "Jane Doe"},
            {"address": "bob@example.com"},
        ]

        result = self.service._build_recipients(recipients)

        assert len(result) == 3
        assert result[0].email_address.address == "john@example.com"
        assert result[1].email_address.address == "jane@example.com"
        assert result[2].email_address.address == "bob@example.com"

    def test_empty_recipients(self):
        """Test building empty recipients list"""
        result = self.service._build_recipients([])

        assert len(result) == 0


class TestMessageToDict:
    """Tests for MailService._message_to_dict method"""

    def setup_method(self):
        self.service = MailService()

    def test_basic_fields(self):
        """Test basic message fields are converted"""
        message = MagicMock()
        message.id = "msg-123"
        message.subject = "Test Subject"
        message.body_preview = "Preview text"
        message.is_draft = True
        message.is_read = False
        message.web_link = "https://outlook.com/mail/123"
        message.body = None
        message.to_recipients = None
        message.cc_recipients = None
        message.bcc_recipients = None
        message.from_ = None
        message.importance = None
        message.created_date_time = None
        message.last_modified_date_time = None

        result = self.service._message_to_dict(message)

        assert result["id"] == "msg-123"
        assert result["subject"] == "Test Subject"
        assert result["bodyPreview"] == "Preview text"
        assert result["isDraft"] is True
        assert result["isRead"] is False
        assert result["webLink"] == "https://outlook.com/mail/123"

    def test_body_conversion(self):
        """Test body field conversion"""
        message = self._make_minimal_message()
        message.body = MagicMock()
        message.body.content_type = "html"
        message.body.content = "<p>Hello world</p>"

        result = self.service._message_to_dict(message)

        assert result["body"]["contentType"] == "html"
        assert result["body"]["content"] == "<p>Hello world</p>"

    def test_to_recipients_conversion(self):
        """Test toRecipients field conversion"""
        message = self._make_minimal_message()
        recipient = MagicMock()
        recipient.email_address = MagicMock()
        recipient.email_address.name = "John Doe"
        recipient.email_address.address = "john@example.com"
        message.to_recipients = [recipient]

        result = self.service._message_to_dict(message)

        assert len(result["toRecipients"]) == 1
        assert result["toRecipients"][0]["emailAddress"]["name"] == "John Doe"
        assert (
            result["toRecipients"][0]["emailAddress"]["address"] == "john@example.com"
        )

    def test_cc_recipients_conversion(self):
        """Test ccRecipients field conversion"""
        message = self._make_minimal_message()
        recipient = MagicMock()
        recipient.email_address = MagicMock()
        recipient.email_address.name = "Jane Doe"
        recipient.email_address.address = "jane@example.com"
        message.cc_recipients = [recipient]

        result = self.service._message_to_dict(message)

        assert len(result["ccRecipients"]) == 1
        assert result["ccRecipients"][0]["emailAddress"]["name"] == "Jane Doe"

    def test_bcc_recipients_conversion(self):
        """Test bccRecipients field conversion"""
        message = self._make_minimal_message()
        recipient = MagicMock()
        recipient.email_address = MagicMock()
        recipient.email_address.name = "Secret"
        recipient.email_address.address = "secret@example.com"
        message.bcc_recipients = [recipient]

        result = self.service._message_to_dict(message)

        assert len(result["bccRecipients"]) == 1
        assert (
            result["bccRecipients"][0]["emailAddress"]["address"]
            == "secret@example.com"
        )

    def test_from_conversion(self):
        """Test from field conversion"""
        message = self._make_minimal_message()
        message.from_ = MagicMock()
        message.from_.email_address = MagicMock()
        message.from_.email_address.name = "Sender"
        message.from_.email_address.address = "sender@example.com"

        result = self.service._message_to_dict(message)

        assert result["from"]["emailAddress"]["name"] == "Sender"
        assert result["from"]["emailAddress"]["address"] == "sender@example.com"

    def test_importance_conversion(self):
        """Test importance field conversion"""
        message = self._make_minimal_message()
        message.importance = "high"

        result = self.service._message_to_dict(message)

        assert result["importance"] == "high"

    def test_timestamps_conversion(self):
        """Test timestamp fields conversion"""
        message = self._make_minimal_message()
        message.created_date_time = datetime(2025, 12, 5, 10, 0, 0, tzinfo=timezone.utc)
        message.last_modified_date_time = datetime(
            2025, 12, 5, 11, 0, 0, tzinfo=timezone.utc
        )

        result = self.service._message_to_dict(message)

        assert "2025-12-05" in result["createdDateTime"]
        assert "2025-12-05" in result["lastModifiedDateTime"]

    def test_null_email_address_in_recipient(self):
        """Test handling null email_address in recipient"""
        message = self._make_minimal_message()
        recipient = MagicMock()
        recipient.email_address = None
        message.to_recipients = [recipient]

        result = self.service._message_to_dict(message)

        assert result["toRecipients"][0]["emailAddress"]["name"] is None
        assert result["toRecipients"][0]["emailAddress"]["address"] is None

    def _make_minimal_message(self):
        """Create a minimal mock message with all required fields"""
        message = MagicMock()
        message.id = "msg-123"
        message.subject = "Test"
        message.body_preview = ""
        message.is_draft = True
        message.is_read = False
        message.web_link = None
        message.body = None
        message.to_recipients = None
        message.cc_recipients = None
        message.bcc_recipients = None
        message.from_ = None
        message.importance = None
        message.created_date_time = None
        message.last_modified_date_time = None
        return message
