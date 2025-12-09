"""Unit tests for MailService"""

from datetime import datetime, timezone
from unittest.mock import MagicMock


from app.services.mail_service import MailService, WELL_KNOWN_FOLDERS


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
        message.received_date_time = None
        message.sent_date_time = None
        message.has_attachments = None
        message.conversation_id = None
        return message


class TestResolveFolderId:
    """Tests for MailService._resolve_folder_id method"""

    def setup_method(self):
        self.service = MailService()

    def test_well_known_folder_inbox(self):
        """Test inbox folder resolution"""
        assert self.service._resolve_folder_id("inbox") == "inbox"
        assert self.service._resolve_folder_id("INBOX") == "inbox"
        assert self.service._resolve_folder_id("Inbox") == "inbox"

    def test_well_known_folder_sent(self):
        """Test sent folder resolution"""
        assert self.service._resolve_folder_id("sent") == "sentitems"
        assert self.service._resolve_folder_id("sentitems") == "sentitems"

    def test_well_known_folder_deleted(self):
        """Test deleted folder resolution"""
        assert self.service._resolve_folder_id("deleted") == "deleteditems"
        assert self.service._resolve_folder_id("deleteditems") == "deleteditems"

    def test_well_known_folder_junk(self):
        """Test junk folder resolution"""
        assert self.service._resolve_folder_id("junk") == "junkemail"
        assert self.service._resolve_folder_id("junkemail") == "junkemail"

    def test_custom_folder_id_passthrough(self):
        """Test custom folder IDs are passed through unchanged"""
        custom_id = "AAMkAGI2TG93AAA="
        assert self.service._resolve_folder_id(custom_id) == custom_id


class TestFormatAsTana:
    """Tests for MailService.format_as_tana method"""

    def setup_method(self):
        self.service = MailService()

    def test_empty_messages(self):
        """Test formatting empty message list"""
        result = self.service.format_as_tana([])
        assert result == "%%tana%%\n- No messages found"

    def test_single_message(self):
        """Test formatting single message"""
        messages = [
            {
                "subject": "Test Email",
                "from": {
                    "emailAddress": {
                        "name": "John Doe",
                        "address": "john@example.com",
                    }
                },
                "receivedDateTime": "2025-12-05T10:00:00Z",
                "bodyPreview": "This is a test email preview.",
                "webLink": "https://outlook.com/mail/123",
            }
        ]

        result = self.service.format_as_tana(messages)

        assert "%%tana%%" in result
        assert "- Test Email #email" in result
        assert "From:: John Doe" in result
        assert "Received:: [[date:2025-12-05T10:00:00Z]]" in result
        assert "Preview:: This is a test email preview." in result
        assert "Link:: https://outlook.com/mail/123" in result

    def test_message_without_subject(self):
        """Test formatting message without subject"""
        messages = [{"from": {"emailAddress": {"name": "Sender"}}}]

        result = self.service.format_as_tana(messages)

        assert "- (No subject) #email" in result

    def test_message_with_address_only(self):
        """Test formatting message with email address but no name"""
        messages = [
            {
                "subject": "Test",
                "from": {
                    "emailAddress": {
                        "name": None,
                        "address": "sender@example.com",
                    }
                },
            }
        ]

        result = self.service.format_as_tana(messages)

        assert "From:: sender@example.com" in result

    def test_deleted_messages_skipped(self):
        """Test that deleted messages are skipped in Tana output"""
        messages = [
            {"subject": "Normal Email"},
            {"subject": "Deleted Email", "@removed": {"reason": "deleted"}},
        ]

        result = self.service.format_as_tana(messages)

        assert "Normal Email" in result
        assert "Deleted Email" not in result

    def test_custom_tag(self):
        """Test custom tag parameter"""
        messages = [{"subject": "Test"}]

        result = self.service.format_as_tana(messages, tag="inbox")

        assert "- Test #inbox" in result

    def test_long_preview_truncated(self):
        """Test that long body previews are truncated"""
        long_preview = "A" * 300
        messages = [{"subject": "Test", "bodyPreview": long_preview}]

        result = self.service.format_as_tana(messages)

        # Should be truncated to 200 chars + "..."
        assert "A" * 200 in result
        assert "..." in result

    def test_preview_newlines_removed(self):
        """Test that newlines in preview are replaced"""
        messages = [{"subject": "Test", "bodyPreview": "Line1\nLine2\rLine3"}]

        result = self.service.format_as_tana(messages)

        # \n becomes space, \r is removed
        assert "Line1 Line2Line3" in result
        # No raw newlines in the preview line itself
        preview_line = [line for line in result.split("\n") if "Preview::" in line][0]
        assert "\r" not in preview_line


class TestWellKnownFolders:
    """Tests for WELL_KNOWN_FOLDERS constant"""

    def test_all_folders_defined(self):
        """Test all expected folders are defined"""
        expected = [
            "inbox",
            "drafts",
            "sent",
            "sentitems",
            "deleted",
            "deleteditems",
            "junk",
            "junkemail",
            "archive",
            "outbox",
        ]

        for folder in expected:
            assert folder in WELL_KNOWN_FOLDERS

    def test_folder_values_are_valid(self):
        """Test all folder values are valid MS Graph folder IDs"""
        valid_ids = {
            "inbox",
            "drafts",
            "sentitems",
            "deleteditems",
            "junkemail",
            "archive",
            "outbox",
        }

        for value in WELL_KNOWN_FOLDERS.values():
            assert value in valid_ids
