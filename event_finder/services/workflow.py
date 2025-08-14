from typing import List, Optional, Dict
import logging

from event_finder.schemas import EventsResponse
from event_finder.core.models import Event, EventType
from event_finder.services.search_ddg import search_duckduckgo
from event_finder.services.firecrawl import extract_urls_content, ExtractedContent
from event_finder.services.llm import get_openai_client, EventList
from event_finder.services.normalize import normalize_url, parse_date
from event_finder.config.settings import OPENAI_API_KEY, TOP_N
from event_finder.core.utils import sort_events_by_date

logger = logging.getLogger(__name__)


async def scrape_with_retry(batch_urls: List[str]) -> List[ExtractedContent]:
    attempt = 0
    max_attempts = 2
    last_results: List[ExtractedContent] = []
    while attempt < max_attempts:
        attempt += 1
        results = await extract_urls_content(batch_urls)
        last_results = results
        # If any succeeded, stop retrying; otherwise retry
        if any(r.success for r in results):
            return results
        logger.warning(f"Firecrawl attempt {attempt} returned no successes for {len(batch_urls)} URLs")
    return last_results

async def find_upcoming_events(user_query: str, filter_event_type: Optional[str] = None) -> EventsResponse:
	"""
	End-to-end workflow:
	user query -> DuckDuckGo search -> Firecrawl scrape URLs -> LLM parse -> sort by date -> return
	Includes robust retries and error handling for DDG and Firecrawl.
	"""
	# 1) DuckDuckGo search with basic retry
	search_results: List[Dict[str, str]] = []
	ddg_attempts = 0
	ddg_max_attempts = 3
	while ddg_attempts < ddg_max_attempts:
		try:
			search_results = search_duckduckgo(user_query, max_results=TOP_N)
			break
		except Exception as e:
			ddg_attempts += 1
			logger.warning(f"DuckDuckGo search attempt {ddg_attempts} failed: {e}")
			if ddg_attempts >= ddg_max_attempts:
				search_results = []
				break
	
	urls: List[str] = []
	for r in search_results:
		url = normalize_url(r.get('url', ''))
		if url:
			urls.append(url)
	# de-duplicate while preserving order
	seen = set()
	deduped_urls: List[str] = []
	for u in urls:
		if u not in seen:
			seen.add(u)
			deduped_urls.append(u)
	urls = deduped_urls[:TOP_N]
	
	if not urls:
		return EventsResponse(speaker=user_query, count=0, events=[])
	
	# 2) Firecrawl scrape with retry (async)
	scrape_results = await scrape_with_retry(urls)
	
	# 3) Build LLM prompt and parse structured events
	successful_pages = [r for r in scrape_results if r.success and (r.markdown or r.html)]
	if not successful_pages:
		return EventsResponse(speaker=user_query, count=0, events=[])
	
	sections: List[str] = []
	for page in successful_pages:
		content = page.markdown or page.html or ""
		sections.append(f"URL: {page.url}\n---\n{content[:8000]}")
	prompt = (
		"Extract a JSON list of upcoming events from the following pages. Use fields: "
		"event_name, date, location{name,address,city,country}, url, speakers[list of strings], event_type in {in_person, online, N/A}.\n"
		"Only include real events.\n\n" + "\n\n".join(sections)
	)
	
	client = get_openai_client(str(OPENAI_API_KEY))
	event_list: EventList = await client.parse_structured_output(prompt)
	events: List[Event] = event_list.events if event_list and event_list.events else []
	
	# 4) Normalize and filter
	filtered: List[Event] = []
	for ev in events:
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
	
	# 5) Sort
	sorted_events = sort_events_by_date(filtered)
	
	return EventsResponse(
		speaker=user_query,
		count=len(sorted_events),
		events=sorted_events
	) 