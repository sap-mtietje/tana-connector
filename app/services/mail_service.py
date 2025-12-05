"""Mail service - MS Graph style responses via Kiota SDK"""

from typing import Optional, List, Dict, Any

from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress

from app.services.graph_service import graph_service


class MailService:
    """Mail operations using Kiota SDK, returning MS Graph format"""

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
            from msgraph.generated.models.importance import Importance

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

        # Timestamps
        if message.created_date_time:
            result["createdDateTime"] = message.created_date_time.isoformat()
        if message.last_modified_date_time:
            result["lastModifiedDateTime"] = message.last_modified_date_time.isoformat()

        return result


mail_service = MailService()
