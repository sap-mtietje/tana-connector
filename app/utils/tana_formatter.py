"""Tana paste format utilities

Tana paste is a plain-text format for pasting structured data into Tana.
This module will be expanded as we understand the format requirements.
"""

from typing import List, Dict, Any


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


