from typing import List
from pydantic import BaseModel
from event_finder.core.models import Event


class EventsResponse(BaseModel):
	events: List[Event]




