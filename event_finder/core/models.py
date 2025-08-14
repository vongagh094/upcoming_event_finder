from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Literal
from enum import Enum
from pydantic import BaseModel


class EventType(str, Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    NOT_AVAILABLE = "N/A"


class Event(BaseModel):
    """Core event data model."""
    url: Optional[str] = "N/A"
    speakers: Optional[List[str]] = []
    event_type: EventType = EventType.NOT_AVAILABLE
    source: Optional[str] = "N/A"
    event_name: Optional[str] = "N/A"
    date: Optional[datetime] = None
    location: Optional[str] = "N/A"
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if not self.speakers:
            self.speakers = []
        if isinstance(self.event_type, str):
            # Convert string to EventType enum
            try:
                self.event_type = EventType(self.event_type)
            except ValueError:
                self.event_type = EventType.NOT_AVAILABLE


class EventsResponse(BaseModel):
    speaker: str
    count: int
    events: List[Event]