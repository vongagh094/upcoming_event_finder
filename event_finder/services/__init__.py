"""
Event Finder Services

This module provides search services for finding events from various sources.
"""

from .search_ddg import search_duckduckgo
from .workflow import find_upcoming_events

__all__ = [
	'search_duckduckgo',
	'find_upcoming_events'
]