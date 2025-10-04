"""Application-wide constants"""


ENUM_DISPLAY_NAMES = {
    "tentativelyaccepted": "Tentative",
    "notresponded": "No Response",
    "oof": "Out of Office",
    "workingelsewhere": "Working Elsewhere",
}

# Description cleanup patterns for "clean" mode
DESCRIPTION_CLEANUP_PATTERNS = [
    r'_{5,}',
    r'={5,}',
    r'\*{5,}',
    r'-{5,}',
    
    # Video conferencing platforms
    r'Join (Zoom|Teams|Meet|Webex|GoToMeeting) Meeting.*',
    r'Join\s+the\s+meeting\s+now\s*',
    r'Meeting ID:.*',
    r'Passcode:.*',
    r'Phone conference ID:.*',
    
    # Meeting URLs (to be handled by smart link preservation)
    r'https?://zoom\.us[^\s]*',
    r'https?://teams\.microsoft\.com[^\s]*',
    r'https?://meet\.google\.com[^\s]*',
    r'https?://[^\s]*\.webex\.com[^\s]*',
    r'https?://[^\s]*\.gotomeeting\.com[^\s]*',
    r'https?://[^\s]*\.bluejeans\.com[^\s]*',
    
    # Generic meeting phrases
    r'Microsoft Teams\s*',
    r'Need help\?\s*',
    r'Dial\s+in\s+by\s+phone\s*',
    r'Find\s+a\s+local\s+number\s*',
    r'For\s+organizers:\s*',
    r'Meeting\s+options.*',
    r'Reset\s+dial-in\s+PIN\s*',
    r'One\s+tap\s+mobile.*',
    
    # Phone numbers and dial-in info
    r'\+?\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}[,#\d]*',
    
    # HTML tags
    r'<[^>]+>',
]

# HTML entities to decode
HTML_ENTITIES = {
    '&nbsp;': ' ',
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&#39;': "'",
    '&apos;': "'",
    '&#x27;': "'",
    '&#x2F;': '/',
    '&#x60;': '`',
    '&#x3D;': '=',
    '&mdash;': '—',
    '&ndash;': '–',
    '&hellip;': '…',
    '&lsquo;': ''',
    '&rsquo;': ''',
    '&ldquo;': '"',
    '&rdquo;': '"',
}

# Meeting platform domains for smart link preservation
MEETING_DOMAINS = [
    'zoom.us',
    'teams.microsoft.com',
    'meet.google.com',
    'webex.com',
    'gotomeeting.com',
    'bluejeans.com',
    'chime.aws',
    'whereby.com',
]


def format_enum(value: str) -> str:
    """Format Graph API enum value for display
    
    Returns friendly name if mapping exists, otherwise capitalizes the value.
    Examples:
        "tentativelyaccepted" -> "Tentative"
        "oof" -> "Out of Office"
        "accepted" -> "Accepted"
        "free" -> "Free"
    """
    if not value:
        return ""
    
    value_lower = value.lower()
    return ENUM_DISPLAY_NAMES.get(value_lower, value_lower.capitalize())

