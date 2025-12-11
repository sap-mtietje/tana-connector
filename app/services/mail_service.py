"""Mail service - MS Graph style responses via Kiota SDK."""

from typing import Optional, List, Dict, Any

from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.importance import Importance
from msgraph.generated.users.item.mail_folders.item.messages.delta.delta_request_builder import (
    DeltaRequestBuilder,
)

from app.constants import WELL_KNOWN_MAIL_FOLDERS
from app.services.graph_service import graph_service
from app.services.delta_cache_service import delta_cache_service
from app.utils.timezone_utils import format_datetime_local


# Alias for backward compatibility
WELL_KNOWN_FOLDERS = WELL_KNOWN_MAIL_FOLDERS


class MailService:
    """Mail operations using Kiota SDK, returning MS Graph format"""

    def _resolve_folder_id(self, folder_id: str) -> str:
        """Resolve well-known folder names to MS Graph folder IDs."""
        return WELL_KNOWN_FOLDERS.get(folder_id.lower(), folder_id)

    async def get_messages_delta(
        self,
        folder_id: str,
        select: Optional[List[str]] = None,
        filter: Optional[str] = None,
        top: Optional[int] = None,
        use_cache: bool = True,
        follow_pagination: bool = True,
    ) -> Dict[str, Any]:
        """
        Get messages delta (new/changed/deleted since last sync).

        Uses cached delta token if available for incremental sync.
        On first call (no cache), returns all messages in the folder.

        Args:
            folder_id: Mail folder ID or well-known name (inbox, sent, etc.)
            select: Fields to return (e.g., ['subject', 'from', 'receivedDateTime'])
            filter: OData filter expression
            top: Maximum number of messages per page
            use_cache: Whether to use cached delta token (default True)
            follow_pagination: Auto-follow @odata.nextLink to get all pages (default True)
                              Set to False to get only the first page.

        Returns:
            Dict with:
            - value: List of message dicts
            - @odata.deltaLink: URL for next sync (only present after all pages fetched)
            - @odata.nextLink: URL for next page (only if follow_pagination=False)
            - _cached: Whether delta token was used from cache
            - _isInitialSync: True if this is a full sync (no prior delta token)
            - _pagesFetched: Number of pages fetched (when follow_pagination=True)
        """
        client = await graph_service.get_client()
        resolved_folder = self._resolve_folder_id(folder_id)

        # Check for cached delta token
        cached_delta_link = None
        if use_cache:
            cached_delta_link = delta_cache_service.get_token(resolved_folder)

        if cached_delta_link:
            # Use cached delta link for incremental sync
            delta_builder = client.me.mail_folders.by_mail_folder_id(
                resolved_folder
            ).messages.delta.with_url(cached_delta_link)
            result = await delta_builder.get()
            is_initial_sync = False
        else:
            # Initial sync - get all messages
            query_params = DeltaRequestBuilder.DeltaRequestBuilderGetQueryParameters(
                select=select,
                filter=filter,
                top=top,
            )
            request_config = RequestConfiguration(
                query_parameters=query_params,
            )

            delta_builder = client.me.mail_folders.by_mail_folder_id(
                resolved_folder
            ).messages.delta
            result = await delta_builder.get(request_configuration=request_config)
            is_initial_sync = True

        if not result:
            return {
                "value": [],
                "_cached": cached_delta_link is not None,
                "_isInitialSync": is_initial_sync,
            }

        # Convert messages to dicts
        messages = []
        pages_fetched = 1

        def process_messages(result_value):
            """Process messages from a result page."""
            if not result_value:
                return
            for msg in result_value:
                msg_dict = self._message_to_dict(msg)
                # Check for deleted items (have @removed property)
                if hasattr(msg, "additional_data") and msg.additional_data:
                    if "@removed" in msg.additional_data:
                        msg_dict["@removed"] = msg.additional_data["@removed"]
                messages.append(msg_dict)

        # Process first page
        process_messages(result.value)

        # Follow pagination to get all pages and the final deltaLink
        if follow_pagination:
            while result.odata_next_link and not result.odata_delta_link:
                # Follow the next link
                delta_builder = client.me.mail_folders.by_mail_folder_id(
                    resolved_folder
                ).messages.delta.with_url(result.odata_next_link)
                result = await delta_builder.get()
                pages_fetched += 1

                if result and result.value:
                    process_messages(result.value)

        # Build response
        response = {
            "value": messages,
            "@odata.count": len(messages),
            "_cached": cached_delta_link is not None,
            "_isInitialSync": is_initial_sync,
            "_pagesFetched": pages_fetched,
        }

        # Include delta/next links
        if result.odata_delta_link:
            response["@odata.deltaLink"] = result.odata_delta_link
            # Auto-cache the delta link for next sync
            if use_cache:
                delta_cache_service.save_token(resolved_folder, result.odata_delta_link)

        if result.odata_next_link:
            response["@odata.nextLink"] = result.odata_next_link

        return response

    async def create_draft(
        self,
        subject: str,
        body_content: str,
        body_content_type: str = "HTML",
        to_recipients: Optional[List[Dict[str, str]]] = None,
        cc_recipients: Optional[List[Dict[str, str]]] = None,
        bcc_recipients: Optional[List[Dict[str, str]]] = None,
        importance: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a draft email message using POST /me/messages.

        Args:
            subject: Email subject
            body_content: Email body content
            body_content_type: "HTML" or "Text"
            to_recipients: List of {"address": "email", "name": "optional name"}
            cc_recipients: List of CC recipients
            bcc_recipients: List of BCC recipients
            importance: "low", "normal", or "high"

        Returns:
            Created draft message in MS Graph JSON format
        """
        client = await graph_service.get_client()

        # Build the message object
        message = Message()
        message.subject = subject

        # Body
        message.body = ItemBody()
        message.body.content = body_content
        message.body.content_type = (
            BodyType.Html if body_content_type.upper() == "HTML" else BodyType.Text
        )

        # Recipients
        if to_recipients:
            message.to_recipients = self._build_recipients(to_recipients)
        if cc_recipients:
            message.cc_recipients = self._build_recipients(cc_recipients)
        if bcc_recipients:
            message.bcc_recipients = self._build_recipients(bcc_recipients)

        # Importance
        if importance:
            importance_map = {
                "low": Importance.Low,
                "normal": Importance.Normal,
                "high": Importance.High,
            }
            message.importance = importance_map.get(
                importance.lower(), Importance.Normal
            )

        # Create the draft
        result = await client.me.messages.post(message)

        return self._message_to_dict(result)

    def format_as_tana(self, messages: List[Dict[str, Any]], tag: str = "email") -> str:
        """
        Format MS Graph messages as Tana Paste.

        Simple default format - for complex formatting, use POST with template.
        """
        if not messages:
            return "%%tana%%\n- No messages found"

        lines = ["%%tana%%"]
        for msg in messages:
            # Skip deleted messages in Tana output
            if "@removed" in msg:
                continue

            subject = msg.get("subject", "(No subject)")
            lines.append(f"- {subject} #{tag}")

            # From
            from_addr = msg.get("from", {})
            if from_addr:
                email_addr = from_addr.get("emailAddress", {})
                sender = email_addr.get("name") or email_addr.get("address", "")
                if sender:
                    lines.append(f"  - From:: {sender}")

            # Received date
            received = msg.get("receivedDateTime")
            if received:
                lines.append(f"  - Received:: [[date:{received}]]")

            # Body preview (truncated)
            preview = msg.get("bodyPreview", "")
            if preview:
                # Truncate and clean up
                preview = preview[:200].replace("\n", " ").replace("\r", "")
                if len(msg.get("bodyPreview", "")) > 200:
                    preview += "..."
                lines.append(f"  - Preview:: {preview}")

            # Web link
            web_link = msg.get("webLink")
            if web_link:
                lines.append(f"  - Link:: {web_link}")

        return "\n".join(lines)

    def _build_recipients(self, recipients: List[Dict[str, str]]) -> List[Recipient]:
        """Convert recipient dicts to Kiota Recipient objects."""
        result = []
        for r in recipients:
            recipient = Recipient()
            recipient.email_address = EmailAddress()
            recipient.email_address.address = r.get("address")
            recipient.email_address.name = r.get("name")
            result.append(recipient)
        return result

    def _message_to_dict(self, message: Message) -> Dict[str, Any]:
        """
        Convert Kiota Message object to dict matching MS Graph JSON format.
        """
        result = {
            "id": message.id,
            "subject": message.subject,
            "bodyPreview": message.body_preview,
            "isDraft": message.is_draft,
            "isRead": message.is_read,
            "webLink": message.web_link,
        }

        # Body
        if message.body:
            result["body"] = {
                "contentType": str(message.body.content_type)
                if message.body.content_type
                else None,
                "content": message.body.content,
            }

        # Recipients
        if message.to_recipients:
            result["toRecipients"] = [
                {
                    "emailAddress": {
                        "name": r.email_address.name if r.email_address else None,
                        "address": r.email_address.address if r.email_address else None,
                    }
                }
                for r in message.to_recipients
            ]

        if message.cc_recipients:
            result["ccRecipients"] = [
                {
                    "emailAddress": {
                        "name": r.email_address.name if r.email_address else None,
                        "address": r.email_address.address if r.email_address else None,
                    }
                }
                for r in message.cc_recipients
            ]

        if message.bcc_recipients:
            result["bccRecipients"] = [
                {
                    "emailAddress": {
                        "name": r.email_address.name if r.email_address else None,
                        "address": r.email_address.address if r.email_address else None,
                    }
                }
                for r in message.bcc_recipients
            ]

        # From
        if message.from_:
            result["from"] = {
                "emailAddress": {
                    "name": message.from_.email_address.name
                    if message.from_.email_address
                    else None,
                    "address": message.from_.email_address.address
                    if message.from_.email_address
                    else None,
                }
            }

        # Importance
        result["importance"] = str(message.importance) if message.importance else None

        # Timestamps (converted to local timezone)
        if message.created_date_time:
            result["createdDateTime"] = format_datetime_local(message.created_date_time)
        if message.last_modified_date_time:
            result["lastModifiedDateTime"] = format_datetime_local(
                message.last_modified_date_time
            )
        if message.received_date_time:
            result["receivedDateTime"] = format_datetime_local(
                message.received_date_time
            )
        if message.sent_date_time:
            result["sentDateTime"] = format_datetime_local(message.sent_date_time)

        # Additional useful fields
        result["hasAttachments"] = message.has_attachments
        result["conversationId"] = message.conversation_id
        result["categories"] = message.categories or []

        return result


mail_service = MailService()
