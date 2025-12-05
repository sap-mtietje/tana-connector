"""Mail endpoints - MS Graph style API"""

from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.services.mail_service import mail_service

router = APIRouter(tags=["Mail"])


class EmailAddressInput(BaseModel):
    """Email address with optional display name"""

    address: str = Field(
        ..., description="Email address", examples=["colleague@company.com"]
    )
    name: Optional[str] = Field(
        default=None, description="Display name", examples=["John Doe"]
    )


class MessageBody(BaseModel):
    """Email body content"""

    contentType: str = Field(
        default="HTML",
        description="Content type: HTML or Text",
        examples=["HTML", "Text"],
    )
    content: str = Field(..., description="Body content", examples=["<p>Hello!</p>"])


class CreateDraftRequest(BaseModel):
    """Request body for creating a draft email"""

    subject: str = Field(
        ..., description="Email subject", examples=["Meeting Follow-up"]
    )
    body: MessageBody = Field(..., description="Email body")
    toRecipients: Optional[List[EmailAddressInput]] = Field(
        default=None, description="To recipients"
    )
    ccRecipients: Optional[List[EmailAddressInput]] = Field(
        default=None, description="CC recipients"
    )
    bccRecipients: Optional[List[EmailAddressInput]] = Field(
        default=None, description="BCC recipients"
    )
    importance: Optional[str] = Field(
        default=None,
        description="Importance level",
        examples=["low", "normal", "high"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subject": "Meeting Follow-up",
                    "body": {
                        "contentType": "HTML",
                        "content": "<p>Thanks for the meeting!</p>",
                    },
                    "toRecipients": [
                        {"address": "colleague@company.com", "name": "John Doe"}
                    ],
                    "importance": "normal",
                }
            ]
        }
    }


@router.post(
    "/messages",
    summary="Create draft email",
    description="""
Create a draft email message. The draft is saved in the Drafts folder.

This mirrors Microsoft Graph API `POST /me/messages`.

## Request Body
- `subject` — Email subject (required)
- `body` — Email body with `contentType` (HTML/Text) and `content` (required)
- `toRecipients` — List of To recipients with `address` and optional `name`
- `ccRecipients` — List of CC recipients
- `bccRecipients` — List of BCC recipients
- `importance` — Priority: `low`, `normal`, `high`

## Response
Returns the created draft message with its ID, which can be used to:
- Edit the draft later
- Send the draft via `POST /me/messages/{id}/send`
- Delete the draft

## Example
```json
{
  "subject": "Meeting Follow-up",
  "body": {
    "contentType": "HTML",
    "content": "<p>Thanks for the meeting!</p>"
  },
  "toRecipients": [
    { "address": "colleague@company.com", "name": "John Doe" }
  ]
}
```

## Use Case
Create email drafts from Tana workflows for review before sending.
""",
)
async def create_draft(request: CreateDraftRequest):
    """Create a draft email message."""
    try:
        # Convert recipients to service format
        to_recipients = None
        cc_recipients = None
        bcc_recipients = None

        if request.toRecipients:
            to_recipients = [r.model_dump() for r in request.toRecipients]
        if request.ccRecipients:
            cc_recipients = [r.model_dump() for r in request.ccRecipients]
        if request.bccRecipients:
            bcc_recipients = [r.model_dump() for r in request.bccRecipients]

        draft = await mail_service.create_draft(
            subject=request.subject,
            body_content=request.body.content,
            body_content_type=request.body.contentType,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            importance=request.importance,
        )

        return draft

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create draft: {str(e)}")
