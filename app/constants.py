"""Application-wide constants."""

__all__ = [
    "WELL_KNOWN_MAIL_FOLDERS",
    "CALENDAR_VIEW_FIELDS",
    "MESSAGE_FIELDS",
    "DEFAULT_MEETING_DURATION",
]

# MS Graph well-known mail folder mappings
WELL_KNOWN_MAIL_FOLDERS = {
    "inbox": "inbox",
    "drafts": "drafts",
    "sent": "sentitems",
    "sentitems": "sentitems",
    "deleted": "deleteditems",
    "deleteditems": "deleteditems",
    "junk": "junkemail",
    "junkemail": "junkemail",
    "archive": "archive",
    "outbox": "outbox",
}

# Available fields for calendar view $select
CALENDAR_VIEW_FIELDS = [
    "id",
    "subject",
    "bodyPreview",
    "body",
    "start",
    "end",
    "location",
    "locations",
    "attendees",
    "organizer",
    "categories",
    "importance",
    "sensitivity",
    "showAs",
    "isAllDay",
    "isCancelled",
    "isOnlineMeeting",
    "onlineMeeting",
    "onlineMeetingUrl",
    "webLink",
    "responseStatus",
    "recurrence",
    "type",
    "hasAttachments",
    "isReminderOn",
    "reminderMinutesBeforeStart",
]

# Available fields for message $select
MESSAGE_FIELDS = [
    "id",
    "subject",
    "bodyPreview",
    "body",
    "from",
    "toRecipients",
    "ccRecipients",
    "bccRecipients",
    "receivedDateTime",
    "sentDateTime",
    "hasAttachments",
    "importance",
    "isRead",
    "isDraft",
    "webLink",
    "conversationId",
]

# ISO 8601 duration defaults
DEFAULT_MEETING_DURATION = "PT1H"  # 1 hour
