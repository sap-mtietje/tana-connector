"""Mail endpoints - MS Graph style API."""

from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.constants import MESSAGE_FIELDS
from app.dependencies import DeltaCacheServiceDep, MailServiceDep, TemplateServiceDep
from app.exceptions import GraphAPIError
from app.models import EmailAddressModel, ItemBodyModel
from app.utils.filter_utils import apply_filter

router = APIRouter(tags=["Mail"])

# Shared docstrings
_DELTA_PARAMS_DOC = """
## How Delta Sync Works

1. **First call**: Returns all messages in the folder + a `@odata.deltaLink`
2. **Subsequent calls**: Use the cached delta token to get only changes:
   - New messages (created since last sync)
   - Modified messages (updated since last sync)
   - Deleted messages (marked with `@removed` property)

The delta token is automatically cached per folder. To force a full resync,
use `_useCache=false` or call `DELETE /me/mailFolders/{folder_id}/messages/delta/cache`.

## Query Parameters
- `select` — Comma-separated fields: `subject,from,receivedDateTime,bodyPreview`
- `top` — Maximum number of messages per page
- `_useCache` — Use cached delta token (default: true)
- `_filter` — Post-fetch filter (see below)

## Post-Fetch Filtering (`_filter`)

Filter messages after fetching using `field:operator:value` syntax.
Multiple conditions separated by comma (AND logic).

**Operators:**
- `eq` — equals (default if omitted)
- `ne` — not equals
- `contains` — string contains (case-insensitive)
- `startswith` / `endswith` — string prefix/suffix
- `gt` / `lt` — greater/less than (numbers or dates)
- `exists` — field exists and is not empty

**Examples:**
- `_filter=categories:tana` — messages with "tana" category
- `_filter=isRead:eq:false` — unread messages
- `_filter=from.emailAddress.address:contains:@sap.com` — from SAP
- `_filter=categories:tana,isRead:eq:false` — tana category AND unread
- `_filter=hasAttachments:eq:true` — with attachments

## Response Fields
- `value` — Array of message objects
- `@odata.deltaLink` — URL for next sync (automatically cached)
- `@odata.nextLink` — URL for next page (if paginated)
- `_cached` — Whether a cached delta token was used
- `_isInitialSync` — True if this is a full sync (no prior cache)
- `_filtered` — True if post-fetch filter was applied
"""


class CreateDraftRequest(BaseModel):
    """Request body for creating a draft email"""

    subject: str = Field(
        ..., description="Email subject", examples=["Meeting Follow-up"]
    )
    body: ItemBodyModel = Field(..., description="Email body")
    toRecipients: Optional[List[EmailAddressModel]] = Field(
        default=None, description="To recipients"
    )
    ccRecipients: Optional[List[EmailAddressModel]] = Field(
        default=None, description="CC recipients"
    )
    bccRecipients: Optional[List[EmailAddressModel]] = Field(
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


# =============================================================================
# Delta Sync Endpoints
# =============================================================================


@router.get(
    "/mailFolders/{folder_id}/messages/delta",
    summary="Get messages delta (incremental sync)",
    description=f"""
Get new, modified, or deleted messages since last sync using MS Graph delta queries.

Mirrors Microsoft Graph API `GET /me/mailFolders/{{folder_id}}/messages/delta`.
{_DELTA_PARAMS_DOC}

## Supported Folders
- `inbox` — Inbox folder
- `sent` or `sentitems` — Sent Items
- `drafts` — Drafts folder
- `deleted` or `deleteditems` — Deleted Items
- `junk` or `junkemail` — Junk Email
- `archive` — Archive folder
- Or any folder ID from MS Graph

## Extension Parameters
- `_format` — Response format: `json` (default) or `tana`

## Examples
```bash
# Initial sync (returns all messages)
GET /me/mailFolders/inbox/messages/delta?top=50

# Incremental sync (uses cached delta token)
GET /me/mailFolders/inbox/messages/delta

# Force full resync
GET /me/mailFolders/inbox/messages/delta?_useCache=false

# Get as Tana Paste
GET /me/mailFolders/inbox/messages/delta?_format=tana
```
""",
)
async def get_messages_delta(
    mail_service: MailServiceDep,
    folder_id: str = Path(
        ...,
        description="Mail folder ID or well-known name (inbox, sent, drafts, etc.)",
        examples=["inbox", "sent", "drafts"],
    ),
    select: Optional[str] = Query(
        default=None,
        description=f"Comma-separated fields to return. Available: {', '.join(MESSAGE_FIELDS[:8])}...",
        examples=["subject,from,receivedDateTime,bodyPreview"],
    ),
    filter: Optional[str] = Query(
        default=None,
        alias="$filter",
        description="OData filter expression",
        examples=["isRead eq false", "hasAttachments eq true"],
    ),
    top: Optional[int] = Query(
        default=None,
        ge=1,
        le=999,
        description="Maximum number of messages per page",
    ),
    _useCache: bool = Query(
        default=True,
        description="Use cached delta token for incremental sync. Set to false for full resync.",
    ),
    _filter: Optional[str] = Query(
        default=None,
        description="Post-fetch filter expression. Format: field:operator:value (comma-separated for AND)",
        examples=[
            "categories:tana",
            "isRead:eq:false",
            "from.emailAddress.address:contains:@sap.com",
        ],
    ),
    _format: str = Query(
        default="json",
        description="Response format",
        examples=["json", "tana"],
        pattern="^(json|tana)$",
    ),
):
    """Get messages delta with automatic caching and optional post-fetch filtering."""
    try:
        # Parse select fields
        select_list = [s.strip() for s in select.split(",")] if select else None

        result = await mail_service.get_messages_delta(
            folder_id=folder_id,
            select=select_list,
            filter=filter,
            top=top,
            use_cache=_useCache,
        )

        # Apply post-fetch filter if specified
        if _filter:
            original_count = len(result.get("value", []))
            result["value"] = apply_filter(result.get("value", []), _filter)
            result["_filtered"] = True
            result["_filterExpression"] = _filter
            result["_filteredCount"] = len(result["value"])
            result["_originalCount"] = original_count

        if _format == "tana":
            tana_output = mail_service.format_as_tana(result.get("value", []))
            return PlainTextResponse(content=tana_output)

        return result

    except Exception as e:
        # Wrap unexpected errors in GraphAPIError for consistent handling
        raise GraphAPIError(
            message=f"Failed to fetch messages delta: {str(e)}",
            details={"error_type": type(e).__name__},
        )


@router.post(
    "/mailFolders/{folder_id}/messages/delta/render",
    summary="Get messages delta with template",
    description=f"""
Get messages delta and render with a custom Jinja2 template.

Same parameters as GET, plus a Jinja2 template in the request body.
{_DELTA_PARAMS_DOC}

## Template Context
- `messages` — List of message objects (MS Graph format)
- `count` — Number of messages
- `folder` — Folder ID used
- `is_initial_sync` — Whether this is a full sync
- `cached` — Whether delta token was used from cache

## Message Fields (MS Graph format)
- `subject`, `bodyPreview`, `body.content`
- `from.emailAddress.name`, `from.emailAddress.address`
- `receivedDateTime`, `sentDateTime`
- `isRead`, `isDraft`, `hasAttachments`
- `importance`, `webLink`
- `@removed` — Present if message was deleted

## Example Template
```jinja2
%%tana%%
{{% for msg in messages %}}
{{% if '@removed' not in msg %}}
- {{{{msg.subject}}}} #email
  - From:: {{{{msg.from.emailAddress.name if msg.from else ''}}}}
  - Received:: [[date:{{{{msg.receivedDateTime}}}}]]
  {{% if msg.bodyPreview %}}
  - Preview:: {{{{msg.bodyPreview[:100]}}}}
  {{% endif %}}
{{% endif %}}
{{% endfor %}}
```
""",
    response_class=PlainTextResponse,
)
async def post_messages_delta_with_template(
    mail_service: MailServiceDep,
    template_service: TemplateServiceDep,
    folder_id: str = Path(..., description="Mail folder ID or well-known name"),
    template_body: str = Body(
        ..., media_type="text/plain", description="Jinja2 template string"
    ),
    select: Optional[str] = Query(default=None),
    filter: Optional[str] = Query(default=None, alias="$filter"),
    top: Optional[int] = Query(default=None, ge=1, le=999),
    _useCache: bool = Query(default=True),
    _filter: Optional[str] = Query(
        default=None,
        description="Post-fetch filter expression. Format: field:operator:value",
        examples=["categories:tana", "isRead:eq:false"],
    ),
):
    """Get messages delta, apply optional filter, and render with custom template."""
    if not template_body or not template_body.strip():
        raise HTTPException(status_code=400, detail="Template body is required")

    # Parse select fields
    select_list = [s.strip() for s in select.split(",")] if select else None

    # Fetch messages and render template
    # TemplateError propagates to global handler for 400 response
    result = await mail_service.get_messages_delta(
        folder_id=folder_id,
        select=select_list,
        filter=filter,
        top=top,
        use_cache=_useCache,
    )

    # Apply post-fetch filter if specified
    messages = result.get("value", [])
    if _filter:
        messages = apply_filter(messages, _filter)

    rendered = template_service.render(
        template_string=template_body,
        messages=messages,
        count=len(messages),
        folder=folder_id,
        is_initial_sync=result.get("_isInitialSync", False),
        cached=result.get("_cached", False),
        filtered=_filter is not None,
        filter_expression=_filter,
    )

    return PlainTextResponse(content=rendered)


@router.delete(
    "/mailFolders/{folder_id}/messages/delta/cache",
    summary="Clear delta cache for folder",
    description="""
Clear the cached delta token for a specific folder, forcing a full resync on next request.

Use this when you want to start fresh or if sync state becomes corrupted.
""",
)
async def clear_delta_cache(
    delta_cache_service: DeltaCacheServiceDep,
    folder_id: str = Path(..., description="Mail folder ID or well-known name"),
):
    """Clear cached delta token for a folder."""
    # Resolve folder name to match cache key
    from app.services.mail_service import WELL_KNOWN_FOLDERS

    resolved_folder = WELL_KNOWN_FOLDERS.get(folder_id.lower(), folder_id)
    cleared = delta_cache_service.clear_token(resolved_folder)

    return {
        "folder": folder_id,
        "resolved": resolved_folder,
        "cleared": cleared,
        "message": "Delta cache cleared. Next request will perform full sync."
        if cleared
        else "No cache existed for this folder.",
    }


@router.get(
    "/mailFolders/{folder_id}/messages/delta/cache",
    summary="Get delta cache info",
    description="Get information about the cached delta token for debugging.",
)
async def get_delta_cache_info(
    delta_cache_service: DeltaCacheServiceDep,
    folder_id: str = Path(..., description="Mail folder ID or well-known name"),
):
    """Get delta cache info for debugging."""
    from app.services.mail_service import WELL_KNOWN_FOLDERS

    resolved_folder = WELL_KNOWN_FOLDERS.get(folder_id.lower(), folder_id)
    cache_info = delta_cache_service.get_cache_info(resolved_folder)

    if cache_info:
        # Don't expose the full delta link (it's very long)
        return {
            "folder": folder_id,
            "resolved": resolved_folder,
            "cached": True,
            "updated_at": cache_info.get("updated_at"),
            "delta_link_preview": cache_info.get("delta_link", "")[:100] + "...",
        }

    return {
        "folder": folder_id,
        "resolved": resolved_folder,
        "cached": False,
        "message": "No delta token cached. First sync will fetch all messages.",
    }


# =============================================================================
# Draft Management Endpoints
# =============================================================================


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
async def create_draft(
    mail_service: MailServiceDep,
    request: CreateDraftRequest,
):
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
        # Wrap unexpected errors in GraphAPIError for consistent handling
        raise GraphAPIError(
            message=f"Failed to create draft: {str(e)}",
            details={"error_type": type(e).__name__},
        )
