from typing import List
from datetime import datetime
from event_finder.core.models import Event


def sort_events_by_date(events: List[Event]) -> List[Event]:
	def sort_key(ev: Event):
		date_val = ev.date
		if isinstance(date_val, datetime):
			return date_val
		return datetime.max
	return sorted(events, key=sort_key)






