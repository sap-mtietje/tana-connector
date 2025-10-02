"""Tana paste format utilities"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class TanaFormatter:
    """Helper class for formatting data into Tana paste format"""
    
    @staticmethod
    def format_node(title: str, children: List[str] = None, fields: Dict[str, Any] = None) -> str:
        """Format a single Tana node with optional children and fields"""
        lines = [f"- {title}"]
        
        if fields:
            for key, value in fields.items():
                lines.append(f"  - {key}:: {value}")
        
        if children:
            for child in children:
                for line in child.split("\n"):
                    lines.append(f"  {line}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_list(items: List[Dict[str, Any]]) -> str:
        """Format a list of items into Tana paste format"""
        nodes = []
        for item in items:
            title = item.get("title", "Untitled")
            fields = item.get("fields", {})
            node = TanaFormatter.format_node(title, fields=fields)
            nodes.append(node)
        
        return "\n".join(nodes)
    
    @staticmethod
    def format_events(
        events: List[Dict[str, Any]], 
        tag: str = "meeting",
        filter_fields: List[str] = None,
        include_category_tags: bool = False,
        show_empty: bool = True,
        field_tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Format calendar events into Tana paste format"""
        lines = []
        field_tags = field_tags or {}
        filter_fields_lower = [f.lower() for f in filter_fields] if filter_fields else []
        
        for event in events:
            title = event.get("title", "Untitled Event")
            title = re.sub(r'^(\d+)\.', r'\1\\.', title)
            
            if include_category_tags and event.get("categories"):
                tags = [f"#[[{cat}]]" for cat in event["categories"] if cat]
                tag_str = " ".join(tags) if tags else f"#[[{tag}]]"
            else:
                tag_str = f"#[[{tag}]]"
            
            lines.append(f"- {title} {tag_str}")
            
            TanaFormatter._add_field(lines, "Identifier", event.get("id"), 
                                      filter_fields_lower, show_empty)
            
            # Date field (combined start/end range)
            if TanaFormatter._should_display("Date", event.get("date"), filter_fields_lower, show_empty):
                date_range = event.get("date")
                if date_range and "/" in date_range:
                    start, end = date_range.split("/")
                    timing = TanaFormatter._format_timing_eventlink(start, end)
                    lines.append(f"  - Date:: {timing}")
            
            # Start field (individual start time)
            if TanaFormatter._should_display("Start", event.get("start"), filter_fields_lower, show_empty):
                lines.append(f"  - Start:: {TanaFormatter._format_single_datetime(event['start'])}")
            
            # End field (individual end time)
            if TanaFormatter._should_display("End", event.get("end"), filter_fields_lower, show_empty):
                lines.append(f"  - End:: {TanaFormatter._format_single_datetime(event['end'])}")
            
            TanaFormatter._add_tagged_field(lines, "Location", event.get("location"), 
                                             field_tags.get("location"), filter_fields_lower, show_empty)
            TanaFormatter._add_field(lines, "Status", event.get("status"), filter_fields_lower, show_empty)
            TanaFormatter._add_field(lines, "Availability", event.get("availability"), filter_fields_lower, show_empty)
            TanaFormatter._add_field(lines, "Importance", event.get("importance"), filter_fields_lower, show_empty)
            TanaFormatter._add_field(lines, "Sensitivity", event.get("sensitivity"), filter_fields_lower, show_empty)
            TanaFormatter._add_bool_field(lines, "Is Cancelled", event.get("is_cancelled"), filter_fields_lower, show_empty)
            TanaFormatter._add_field(lines, "Web Link", event.get("web_link"), filter_fields_lower, show_empty)
            TanaFormatter._add_bool_field(lines, "Is Online Meeting", event.get("is_online_meeting"), filter_fields_lower, show_empty)
            TanaFormatter._add_field(lines, "Online Meeting URL", event.get("online_meeting_url"), filter_fields_lower, show_empty)
            TanaFormatter._add_tagged_field(lines, "Organizer", event.get("organizer"), 
                                             field_tags.get("organizer"), filter_fields_lower, show_empty)
            
            TanaFormatter._add_list_field(lines, "Attendees", event.get("attendees", []), 
                                           field_tags.get("attendees"), filter_fields_lower, show_empty)
            TanaFormatter._add_list_field(lines, "Categories", event.get("categories", []), 
                                           field_tags.get("categories"), filter_fields_lower, show_empty, prefix="[[", suffix="]]")
            
            if TanaFormatter._should_display("Reminder", event.get("is_reminder_on"), filter_fields_lower, show_empty):
                if event.get("is_reminder_on"):
                    minutes = event.get("reminder_minutes", 0)
                    lines.append(f"  - Reminder:: {minutes} minutes before")
            
            TanaFormatter._add_bool_field(lines, "Is Recurring", event.get("is_recurring"), filter_fields_lower, show_empty)
            TanaFormatter._add_field(lines, "Recurrence Pattern", event.get("recurrence_pattern"), filter_fields_lower, show_empty)
            TanaFormatter._add_bool_field(lines, "Has Attachments", event.get("has_attachments"), filter_fields_lower, show_empty)
            
            if TanaFormatter._should_display("Description", event.get("description"), filter_fields_lower, show_empty):
                description = event["description"].replace("\n", " ").replace("\r", "")
                lines.append(f"  - Description:: {description}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _should_display(field: str, value, filter_fields: List[str], show_empty: bool) -> bool:
        """Check if field should be displayed"""
        if filter_fields and field.lower() not in filter_fields:
            return False
        if not show_empty and not TanaFormatter._has_value(value):
            return False
        return True
    
    @staticmethod
    def _has_value(value) -> bool:
        """Check if value is not empty"""
        if value is None or value == "":
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, list) and not value:
            return False
        return True
    
    @staticmethod
    def _add_field(lines: List[str], name: str, value, filter_fields: List[str], show_empty: bool):
        """Add a simple field to lines"""
        if TanaFormatter._should_display(name, value, filter_fields, show_empty):
            lines.append(f"  - {name}:: {value or ''}")
    
    @staticmethod
    def _add_bool_field(lines: List[str], name: str, value, filter_fields: List[str], show_empty: bool):
        """Add a boolean field to lines"""
        if TanaFormatter._should_display(name, value, filter_fields, show_empty):
            lines.append(f"  - {name}:: {str(value).lower()}")
    
    @staticmethod
    def _add_tagged_field(lines: List[str], name: str, value, tag: Optional[str], filter_fields: List[str], show_empty: bool):
        """Add a field with optional tag to lines"""
        if TanaFormatter._should_display(name, value, filter_fields, show_empty):
            if value and value.strip() and tag:
                lines.append(f"  - {name}:: [[{value} #{tag}]]")
            else:
                lines.append(f"  - {name}:: {value or ''}")
    
    @staticmethod
    def _add_list_field(lines: List[str], name: str, items: List[str], tag: Optional[str], 
                        filter_fields: List[str], show_empty: bool, prefix: str = "", suffix: str = ""):
        """Add a list field to lines"""
        if TanaFormatter._should_display(name, items, filter_fields, show_empty) and items:
            lines.append(f"  - {name}:: ")
            for item in items:
                if tag:
                    lines.append(f"    - {prefix}{item} #{tag}{suffix}")
                else:
                    lines.append(f"    - {prefix}{item}{suffix}")
    
    @staticmethod
    def _format_timing_eventlink(start: str, end: str) -> str:
        """Format start and end times as Tana date range"""
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '').replace('.0000000', ''))
            end_dt = datetime.fromisoformat(end.replace('Z', '').replace('.0000000', ''))
            return f"[[date:{start_dt:%Y-%m-%d %H:%M}/{end_dt:%Y-%m-%d %H:%M}]]"
        except Exception:
            return f"[[date:{start}/{end}]]"
    
    @staticmethod
    def _format_single_datetime(dt_str: str) -> str:
        """Format a single datetime as Tana date"""
        try:
            clean_str = dt_str.replace('Z', '').replace('.0000000', '')
            if 'T' in clean_str:
                dt = datetime.fromisoformat(clean_str)
                return f"[[date:{dt:%Y-%m-%d %H:%M}]]"
            return f"[[date:{dt_str}]]"
        except Exception:
            return f"[[date:{dt_str}]]"
