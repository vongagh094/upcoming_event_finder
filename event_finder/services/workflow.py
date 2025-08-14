from typing import List, Optional
import logging
from datetime import datetime

from event_finder.schemas import EventsResponse
from event_finder.core.models import Event, EventType, ListEvent
from event_finder.services.serper import get_serper_client
from event_finder.services.firecrawl import extract_urls_content
from event_finder.services.open_ai import get_openai_client
from event_finder.services.normalize import parse_date, normalize_url, get_domain_from_url
from event_finder.core.utils import sort_events_by_date, build_search_queries
from event_finder.config.lists import EXCLUDE_DOMAINS
from event_finder.config.settings import TOP_N

logger = logging.getLogger(__name__)


async def extract_urls(batch_urls: List[str], speaker: str) -> ListEvent:
    import asyncio
    # Split URLs into batches of 5
    batch_size = 5
    batches = [batch_urls[i:i + batch_size] for i in range(0, len(batch_urls), batch_size)]
    
    # Process all batches concurrently
    batch_tasks = [extract_urls_content(batch, speaker) for batch in batches]
    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
    
    # Collect successful results and handle exceptions
    successful_results = []
    for i, result in enumerate(batch_results):
        try:
            if isinstance(result, ListEvent) and len(result.events) > 0:
                successful_results.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Batch {i} extraction failed: {result}")
            else:
                # Handle case where result is ListEvent but with no events
                logger.info(f"Batch {i} returned no events")
        except Exception as e:
            logger.error(f"Error processing batch {i} result: {e}")
            # Continue to next batch instead of failing entirely
            continue
    
    # Merge all successful results into one ListEvent with error handling

    merged_events = []
    print(f"successful_results: {successful_results}")
    for result in successful_results:
        try:
            if result and hasattr(result, 'events') and result.events:
                merged_events.extend(result.events)
        except Exception as e:
            logger.error(f"Error merging events from result: {e}")
            # Skip this result and continue with others
            continue
    
    return ListEvent(events=merged_events)

def deduplicate_and_filter_past_events(events: List[Event]) -> List[Event]:
	"""Deduplicate events by date and event_name."""
	from datetime import timezone
	
	deduplicated_events = []
	seen_events = set()  # Store tuples of (event_name, date) for deduplication
	
	# Get current time - make it timezone-aware if needed
	now = datetime.now()
	
	for ev in events:
		if ev.date and ev.event_name:
			# Compare only dates (ignore time and timezone)
			event_date = ev.date.date()
			current_date = now.date()
			
			# Only include events today or in the future
			if event_date >= current_date:
				# Create a key from event name and date for deduplication
				event_key = (ev.event_name, ev.date)
				if event_key not in seen_events:
					seen_events.add(event_key)
					deduplicated_events.append(ev)
				else:
					logger.warning(f"Skipping duplicate event: {ev.event_name} on {ev.date}")
			else:
				logger.info(f"Skipping past event: {ev.event_name} on {ev.date}")
		else:
			logger.warning(f"Skipping event with missing date or name: {ev.url}")
	
	return deduplicated_events

async def find_upcoming_events(user_query: str, filter_event_type: Optional[str] = None) -> EventsResponse:
	"""
	End-to-end workflow:
	user query -> DuckDuckGo search -> Firecrawl scrape URLs -> LLM parse -> sort by date -> return
	Includes robust retries and error handling for DDG and Firecrawl.
	"""
	# get dependencies
	# 1) DuckDuckGo search with basic retry
	serper_client = get_serper_client()
	openai_client = get_openai_client()
	print(f"OpenAI client: {openai_client}")

	queries = build_search_queries(user_query)
	search_results = await serper_client.batch_search(queries)

	# deduplicate urls and filter out excluded domains
	existed_domains = []
	urls = []
	for result in search_results.results:
		if result.url is None:
			continue
		normalized_url = normalize_url(result.url)
		domain = get_domain_from_url(normalized_url)
		if domain not in EXCLUDE_DOMAINS and domain not in existed_domains:
			existed_domains.append(domain)
			urls.append(normalized_url)
	print(f"urls: {urls}")
	
	if len(urls) == 0:
		return EventsResponse(speaker=user_query, count=0, events=[])
	
	# 2) Firecrawl scrape with retry (async)
	scrape_results = await extract_urls(urls[:TOP_N], user_query)

	print(f"scrape_results: {scrape_results}")
	
	# 3) Build LLM prompt and parse structured events
	if len(scrape_results.events) == 0:
		return EventsResponse(speaker=user_query, count=0, events=[])
	


	# prompt = (
	# 	"Extract a JSON list of upcoming events from the following pages. Use fields: "
	# 	"event_name, date, location{name,address,city,country}, url, speakers[list of strings], event_type in {in_person, online, N/A}.\n"
	# 	"Only include real events.\n\n" + data_str
	# )
	# event_list: ListEvent = await openai_client.parse_structured_output(prompt)
	# events: List[Event] = event_list.events if event_list and event_list.events else []
	
	# 4) Normalize and filter
	filtered: List[Event] = []
	for ev in scrape_results.events:
		# Normalize date
		parsed = parse_date(ev.date)
		ev.date = parsed
		# Filter event type if requested
		if filter_event_type:
			try:
				etype = EventType(filter_event_type)
			except Exception:
				etype = None
			if etype and ev.event_type != etype:
				continue
		filtered.append(ev)
	# deduplicate events by urls
	deduplicated_events = deduplicate_and_filter_past_events(filtered)
	# 5) Sort
	sorted_events = sort_events_by_date(deduplicated_events)
	
	return EventsResponse(
		speaker=user_query,
		count=len(sorted_events),
		events=sorted_events
	) 