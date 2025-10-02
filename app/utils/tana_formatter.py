"""Tana paste format utilities

Tana paste is a plain-text format for pasting structured data into Tana.
This module will be expanded as we understand the format requirements.
"""

import re
from typing import List, Dict, Any
from datetime import datetime


class TanaFormatter:
    """Helper class for formatting data into Tana paste format"""
    
    @staticmethod
    def format_node(title: str, children: List[str] = None, fields: Dict[str, Any] = None) -> str:
        """
        Format a single Tana node
        
        Args:
            title: The node title
            children: Optional list of child node strings
            fields: Optional dictionary of field values
        
        Returns:
            Formatted Tana paste string
        """
        lines = [f"- {title}"]
        
        # Add fields
        if fields:
            for key, value in fields.items():
                lines.append(f"  - {key}:: {value}")
        
        # Add children
        if children:
            for child in children:
                # Indent child lines
                child_lines = child.split("\n")
                for line in child_lines:
                    lines.append(f"  {line}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_list(items: List[Dict[str, Any]]) -> str:
        """
        Format a list of items into Tana paste format
        
        Args:
            items: List of dictionaries with 'title' and optional 'fields'
        
        Returns:
            Formatted Tana paste string
        """
        nodes = []
        for item in items:
            title = item.get("title", "Untitled")
            fields = item.get("fields", {})
            node = TanaFormatter.format_node(title, fields=fields)
            nodes.append(node)
        
        return "\n".join(nodes)
    
    @staticmethod
    def format_events(events: List[Dict[str, Any]], tag: str = "meeting", 
                     timing_field: str = "Timing", filter_fields: List[str] = None) -> str:
        """Format calendar events into Tana paste format (EventLink compatible)"""
        lines = []
        
        filter_fields_lower = [f.lower() for f in filter_fields] if filter_fields else []
        
        def should_show_field(field: str) -> bool:
            return not filter_fields or field.lower() not in filter_fields_lower
        
        for event in events:
            title = event.get("title", "Untitled Event")
            title = re.sub(r'^(\d+)\.', r'\1\\.', title)
            lines.append(f"- {title} #[[{tag}]]")
            
            if not filter_fields or should_show_field("Identifier"):
                if event.get("id"):
                    lines.append(f"  - Identifier:: {event['id']}")
            
            if not filter_fields or should_show_field(timing_field):
                start, end = event.get("start"), event.get("end")
                if start and end:
                    timing = TanaFormatter._format_timing_eventlink(start, end)
                    lines.append(f"  - {timing_field}:: {timing}")
            
            if not filter_fields or should_show_field("Start"):
                if event.get("start"):
                    lines.append(f"  - Start:: {TanaFormatter._format_single_datetime(event['start'])}")
            
            if not filter_fields or should_show_field("End"):
                if event.get("end"):
                    lines.append(f"  - End:: {TanaFormatter._format_single_datetime(event['end'])}")
            
            if not filter_fields or should_show_field("Location"):
                if event.get("location"):
                    lines.append(f"  - Location:: {event['location']}")
            
            if not filter_fields or should_show_field("Status"):
                if event.get("status"):
                    lines.append(f"  - Status:: {event['status']}")
            
            if not filter_fields or should_show_field("Availability"):
                if event.get("availability"):
                    lines.append(f"  - Availability:: {event['availability']}")
            
            if not filter_fields or should_show_field("Attendees"):
                attendees = event.get("attendees", [])
                if attendees:
                    lines.append("  - Attendees:: ")
                    for attendee in attendees:
                        lines.append(f"    - {attendee}")
            
            if not filter_fields or should_show_field("Description"):
                if event.get("description"):
                    description = event["description"].replace("\n", "").replace("\r", "")
                    lines.append(f"  - Description:: {description}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_timing_eventlink(start: str, end: str) -> str:
        """Format start and end times: [[date:YYYY-MM-DD HH:MM/YYYY-MM-DD HH:MM]]"""
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '').replace('.0000000', ''))
            end_dt = datetime.fromisoformat(end.replace('Z', '').replace('.0000000', ''))
            start_str = start_dt.strftime("%Y-%m-%d %H:%M")
            end_str = end_dt.strftime("%Y-%m-%d %H:%M")
            return f"[[date:{start_str}/{end_str}]]"
        except Exception:
            return f"[[date:{start}/{end}]]"
    
    @staticmethod
    def _format_single_datetime(dt_str: str) -> str:
        """Format a single datetime: [[date:YYYY-MM-DD HH:MM]]"""
        try:
            clean_str = dt_str.replace('Z', '').replace('.0000000', '')
            if 'T' in clean_str:
                dt = datetime.fromisoformat(clean_str)
                return f"[[date:{dt.strftime('%Y-%m-%d %H:%M')}]]"
            return f"[[date:{dt_str}]]"
        except Exception:
            return f"[[date:{dt_str}]]"


