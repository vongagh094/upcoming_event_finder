from typing import List
from datetime import datetime
from event_finder.core.models import Event
from event_finder.config.lists import QUERY_TEMPLATES

def sort_events_by_date(events: List[Event]) -> List[Event]:
	def sort_key(ev: Event):
		date_val = ev.date
		if isinstance(date_val, datetime):
			return date_val
		return datetime.max
	return sorted(events, key=sort_key)


def build_search_queries(user_query: str) -> List[str]:
	"""
	Build a list of search queries based on the user query.
	"""
	queries = []
	for template in QUERY_TEMPLATES:
		queries.append(template.format(user_query))
	return queries



