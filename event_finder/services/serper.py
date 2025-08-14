import requests
import logging
from typing import List, Literal
from event_finder.config.settings import SERPER_API_KEY, TOP_N
from event_finder.core.models import SerperSearchResults, SerperSearchResult

logger = logging.getLogger(__name__)

SERPER_API_URLS = {
    "search": "https://google.serper.dev/search",
}
SearchType = Literal["search", "news"]

_serper_client = None

class SerperSearchService:
    def __init__(self, api_key: str, timeout: int = 10):
        if not api_key:
            raise ValueError("Serper API key is required. Get one at https://serper.dev")
        self.headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        self.api_key = api_key
        self.timeout = timeout

    async def batch_search(
        self, 
        queries: List[str], 
        search_type: SearchType = "search", 
    ) -> SerperSearchResults:
        """
        Perform multiple searches in one request.
        Returns a list of result lists (one per query).
        """
        max_results = TOP_N
        payload = [{"q": q, "num": max_results} for q in queries]
        try:
            resp = requests.post(
                SERPER_API_URLS[search_type],
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()
            results_list = resp.json()  # This will be a list of responses
            output = []
            for results in results_list:
                if search_type == "search" and "organic" in results:
                    for r in results["organic"][:max_results]:
                        output.append(SerperSearchResult(
                            title=r.get("title", ""),
                            url=r.get("link", ""),
                            snippet=r.get("snippet", ""),
                            source="serper"
                        ))
                else:
                    output = []
            return SerperSearchResults(results=output)
        except Exception as e:
            logger.error(f"Batch {search_type} search failed: {e}")
            return SerperSearchResults(results=[])
        
def get_serper_client() -> SerperSearchService:
    """Get the global Serper client instance."""
    global _serper_client
    if _serper_client is None:
        _serper_client = SerperSearchService(api_key=str(SERPER_API_KEY))
    return _serper_client