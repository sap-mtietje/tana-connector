"""Default Jinja2 templates for MCP tool responses.

These templates produce compact, LLM-friendly output that includes all key fields
while avoiding the massive HTML body payloads that bloat raw JSON responses.

Custom templates can be passed via the `template` parameter on any MCP tool
to override these defaults. The same Jinja2 filters are available:
  - clean: Strip HTML tags, collapse whitespace (uses BeautifulSoup)
  - truncate(n): Truncate to n characters at word boundary (default 100)
  - date_format(fmt): Format ISO datetime string (default "%Y-%m-%d %H:%M")
"""

# Template for outlook_get_events
# Context: events (list), count (int)
GET_EVENTS = """\
Found {{ count }} event(s).
{% for event in events %}

---
## {{ loop.index }}. {{ event.subject or "(No subject)" }}
- **ID**: {{ event.id }}
- **When**: {{ event.start.dateTime | date_format }} — {{ event.end.dateTime | date_format }}{% if event.start.timeZone %} ({{ event.start.timeZone }}){% endif %}
{% if event.isAllDay %}- **All Day**: yes
{% endif %}\
{% if event.location and event.location.displayName %}- **Location**: {{ event.location.displayName }}
{% endif %}\
{% if event.isOnlineMeeting and event.onlineMeeting and event.onlineMeeting.joinUrl %}- **Teams Link**: {{ event.onlineMeeting.joinUrl }}
{% endif %}\
{% if event.organizer and event.organizer.emailAddress %}- **Organizer**: {{ event.organizer.emailAddress.name or event.organizer.emailAddress.address }}
{% endif %}\
{% if event.attendees %}- **Attendees**: {% for att in event.attendees %}{{ att.emailAddress.name or att.emailAddress.address }}{% if att.status and att.status.response %} ({{ att.status.response }}){% endif %}{% if not loop.last %}, {% endif %}{% endfor %}

{% endif %}\
{% if event.responseStatus and event.responseStatus.response %}- **Your RSVP**: {{ event.responseStatus.response }}
{% endif %}\
{% if event.showAs %}- **Show As**: {{ event.showAs }}
{% endif %}\
{% if event.importance and event.importance != "normal" %}- **Importance**: {{ event.importance }}
{% endif %}\
{% if event.sensitivity and event.sensitivity != "normal" %}- **Sensitivity**: {{ event.sensitivity }}
{% endif %}\
{% if event.categories %}- **Categories**: {{ event.categories | join(", ") }}
{% endif %}\
{% if event.hasAttachments %}- **Has Attachments**: yes
{% endif %}\
{% if event.recurrence and event.recurrence.pattern %}- **Recurrence**: {{ event.recurrence.pattern.type }}{% if event.recurrence.pattern.interval and event.recurrence.pattern.interval > 1 %} (every {{ event.recurrence.pattern.interval }}){% endif %}

{% endif %}\
{% if event.isCancelled %}- **CANCELLED**
{% endif %}\
{% if event.body and event.body.content %}- **Description**: {{ event.body.content | clean | truncate(500) }}
{% endif %}\
{% if event.webLink %}- **Link**: {{ event.webLink }}
{% endif %}\
{% endfor %}"""

# Template for outlook_create_event
# Context: event (dict)
CREATE_EVENT = """\
Event created: **{{ event.subject }}**
- **ID**: {{ event.id }}
- **When**: {{ event.start.dateTime | date_format }} — {{ event.end.dateTime | date_format }}
{% if event.location and event.location.displayName %}- **Location**: {{ event.location.displayName }}
{% endif %}\
{% if event.isOnlineMeeting and event.onlineMeeting and event.onlineMeeting.joinUrl %}- **Teams Link**: {{ event.onlineMeeting.joinUrl }}
{% endif %}\
{% if event.attendees %}- **Attendees**: {% for att in event.attendees %}{{ att.emailAddress.name or att.emailAddress.address }}{% if not loop.last %}, {% endif %}{% endfor %}

{% endif %}\
{% if event.webLink %}- **Link**: {{ event.webLink }}
{% endif %}"""

# Template for outlook_find_meeting_times
# Context: suggestions (list), count (int), empty_suggestions_reason (str)
FIND_MEETING_TIMES = """\
{% if not suggestions %}\
No available meeting times found. Reason: {{ empty_suggestions_reason or "Unknown" }}
{% else %}\
Found {{ count }} suggestion(s).
{% for sugg in suggestions %}

### Option {{ loop.index }}
- **Time**: {{ sugg.meetingTimeSlot.start.dateTime | date_format }} — {{ sugg.meetingTimeSlot.end.dateTime | date_format }}
- **Confidence**: {{ sugg.confidence }}%
{% if sugg.organizerAvailability %}- **Your availability**: {{ sugg.organizerAvailability }}
{% endif %}\
{% if sugg.suggestionReason %}- **Reason**: {{ sugg.suggestionReason }}
{% endif %}\
{% if sugg.attendeeAvailability %}- **Attendees**:
{% for att in sugg.attendeeAvailability %}  - {{ att.attendee.emailAddress.address }}: {{ att.availability }}
{% endfor %}\
{% endif %}\
{% if sugg.locations %}  - **Locations**: {% for loc in sugg.locations %}{{ loc.displayName }}{% if not loop.last %}, {% endif %}{% endfor %}

{% endif %}\
{% endfor %}\
{% endif %}"""

# Template for outlook_get_emails
# Context: messages (list), count (int), folder (str)
GET_EMAILS = """\
Found {{ count }} message(s) in {{ folder }}.
{% for msg in messages %}

---
## {{ loop.index }}. {{ msg.subject or "(No subject)" }}{% if not msg.isRead %} [UNREAD]{% endif %}

- **ID**: {{ msg.id }}
- **From**: {{ msg.from.emailAddress.name or msg.from.emailAddress.address if msg.from and msg.from.emailAddress else "Unknown" }}
- **Received**: {{ msg.receivedDateTime | date_format }}
{% if msg.toRecipients %}- **To**: {% for r in msg.toRecipients %}{{ r.emailAddress.name or r.emailAddress.address }}{% if not loop.last %}, {% endif %}{% endfor %}

{% endif %}\
{% if msg.ccRecipients %}- **CC**: {% for r in msg.ccRecipients %}{{ r.emailAddress.name or r.emailAddress.address }}{% if not loop.last %}, {% endif %}{% endfor %}

{% endif %}\
{% if msg.importance and msg.importance != "normal" %}- **Importance**: {{ msg.importance }}
{% endif %}\
{% if msg.hasAttachments %}- **Has Attachments**: yes
{% endif %}\
{% if msg.isDraft %}- **Draft**: yes
{% endif %}\
{% if msg.categories %}- **Categories**: {{ msg.categories | join(", ") }}
{% endif %}\
{% if msg.body and msg.body.content %}- **Body**: {{ msg.body.content | clean | truncate(1000) }}
{% elif msg.bodyPreview %}- **Preview**: {{ msg.bodyPreview }}
{% endif %}\
{% if msg.webLink %}- **Link**: {{ msg.webLink }}
{% endif %}\
{% endfor %}"""

# Template for outlook_create_draft
# Context: draft (dict)
CREATE_DRAFT = """\
Draft created: **{{ draft.subject }}**
- **ID**: {{ draft.id }}
{% if draft.toRecipients %}- **To**: {% for r in draft.toRecipients %}{{ r.emailAddress.address }}{% if not loop.last %}, {% endif %}{% endfor %}

{% endif %}\
{% if draft.ccRecipients %}- **CC**: {% for r in draft.ccRecipients %}{{ r.emailAddress.address }}{% if not loop.last %}, {% endif %}{% endfor %}

{% endif %}\
{% if draft.bccRecipients %}- **BCC**: {% for r in draft.bccRecipients %}{{ r.emailAddress.address }}{% if not loop.last %}, {% endif %}{% endfor %}

{% endif %}\
{% if draft.importance and draft.importance != "normal" %}- **Importance**: {{ draft.importance }}
{% endif %}\
{% if draft.webLink %}- **Link**: {{ draft.webLink }}
{% endif %}"""
