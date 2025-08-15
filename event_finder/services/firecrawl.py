"""
Firecrawl integration for batch URL content extraction.

This service handles batch scraping of URLs using the Firecrawl API,
with proper error handling and timeout management.
"""
import logging
from typing import List
from event_finder.core.models import ListEvent
from firecrawl import FirecrawlApp
from event_finder.config.lists import extract_schema
from event_finder.config.settings import FIRECRAWL_API_KEY

logger = logging.getLogger(__name__)

# Global client instance
_firecrawl_client = None
class FirecrawlClient:
    """Client for Firecrawl batch URL extraction."""
    
    def __init__(self):
        """
        Initialize Firecrawl client.
        
        Args:
            timeout: Request timeout in seconds.
        """
        self.api_key = str(FIRECRAWL_API_KEY)
        self.client = None
        
        if not self.api_key or self.api_key == "":
            logger.warning("No Firecrawl API key provided. Service will be disabled.")
            self._enabled = False
        else:
            self._enabled = True
            self.client = FirecrawlApp(api_key=self.api_key)
    
    def is_enabled(self) -> bool:
        """Check if Firecrawl service is enabled (has valid API key)."""
        return self._enabled
    
    def _batch_extract(self, urls: List[str], speaker: str) -> ListEvent:
        """
        Synchronous batch scraping using Firecrawl v1 batch_scrape_urls API.
        
        Args:
            urls: List of URLs to scrape.
            
        Returns:
            List of ExtractedContent objects.
        """
        results: ListEvent = []
        
        try:

            logger.debug(f"Calling Firecrawl extract with {len(urls)} URLs")
            response = self.client.extract(
                urls=urls,
                schema=extract_schema,
                prompt=f"""Extract a JSON list of upcoming events from the following pages. Use fields: 
                event_name, date, location{{name,address,city,country}}, url, speakers[list of strings], event_type in {{in_person, online, N/A}}.
                Only include real events. For each event, include the event name, date, location, url, speakers, and event type.
                Handle missing fields gracefully. Only include events that has {speaker} as one of the speakers.""",
            )
            if not response.success:
                logger.error("Invalid response from Firecrawl batch_scrape_urls API")
                return ListEvent(events=[])
            
            events = response.data.get("events", [])
            results = ListEvent.model_validate({"events": events})
            logger.info(f"Batch extraction completed: {len(results.events)} events found")
           
            return ListEvent(events=results.events)
        except Exception as e:
            logger.error(f"Firecrawl batch_extract failed: {e}")
            return ListEvent(events=[])
    

def get_firecrawl_client() -> FirecrawlClient:
    """Get the global Firecrawl client instance."""
    global _firecrawl_client
    if _firecrawl_client is None:
        _firecrawl_client = FirecrawlClient()
    return _firecrawl_client


async def extract_urls_content(urls: List[str], speaker: str) -> ListEvent:
    """
    Convenience function to extract content from URLs using the global client.
    
    Args:
        urls: List of URLs to extract content from.
        
    Returns:
        List of ExtractedContent objects.
    """
    client = get_firecrawl_client()
    results = client._batch_extract(urls, speaker)
    return results