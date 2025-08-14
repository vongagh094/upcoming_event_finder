from datetime import datetime
from typing import List
from pydantic import BaseModel
from event_finder.core.models import Event


class EventsResponse(BaseModel):
	speaker: str
	count: int
	events: List[Event]




