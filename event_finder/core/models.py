from typing import List, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime


class EventType(str, Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    NOT_AVAILABLE = "N/A"


class Location(BaseModel):
    """Location data model."""
    name: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    country: Optional[str] = ""


class Event(BaseModel):
    """Core event data model."""
    url: Optional[str] = "N/A"
    speakers: Optional[List[str]] = []
    event_type: EventType = EventType.NOT_AVAILABLE
    event_name: Optional[str] = "N/A"
    date: Optional[datetime] = None
    location: Optional[Location] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if not self.speakers:
            self.speakers = []
        if isinstance(self.event_type, str):
            try:
                self.event_type = EventType(self.event_type)
            except ValueError:
                self.event_type = EventType.NOT_AVAILABLE


class EventsResponse(BaseModel):
    speaker: str
    count: int
    events: List[Event]

class SerperSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str

class SerperSearchResults(BaseModel):
    results: List[SerperSearchResult]

class ListEvent(BaseModel):
    events: List[Event]
