"""
Firecrawl integration for batch URL content extraction.

This service handles batch scraping of URLs using the Firecrawl API,
with proper error handling and timeout management.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from firecrawl import FirecrawlApp
from event_finder.config.settings import FIRECRAWL_API_KEY, FIRECRAWL_TIMEOUT

logger = logging.getLogger(__name__)



@dataclass
class ExtractedContent:
    """Represents content extracted from a URL."""
    url: str
    markdown: Optional[str] = None
    html: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None


class FirecrawlClient:
    """Client for Firecrawl batch URL extraction."""
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = FIRECRAWL_TIMEOUT):
        """
        Initialize Firecrawl client.
        
        Args:
            api_key: Firecrawl API key. If None, uses FIRECRAWL_API_KEY from settings.
            timeout: Request timeout in seconds.
        """
        if api_key is None:
            self.api_key = str(FIRECRAWL_API_KEY)
        else:
            self.api_key = str(api_key)
        
        self.timeout = timeout
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
    
    async def extract_batch(self, urls: List[str]) -> List[ExtractedContent]:
        """
        Extract content from multiple URLs using Firecrawl batch API.
        
        Args:
            urls: List of URLs to extract content from.
            
        Returns:
            List of ExtractedContent objects, one per URL.
            Failed extractions will have success=False and error message.
        """
        if not self.is_enabled():
            logger.error("Firecrawl client is not enabled (missing API key)")
            return [
                ExtractedContent(
                    url=url,
                    success=False,
                    error="Firecrawl API key not configured"
                )
                for url in urls
            ]
        
        if not urls:
            return []
        
        logger.info(f"Starting batch extraction for {len(urls)} URLs")
        
        try:
            # Run the batch extraction with timeout
            result = await asyncio.wait_for(
                self._run_batch_extraction(urls),
                timeout=self.timeout
            )
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Firecrawl batch extraction timed out after {self.timeout}s")
            return [
                ExtractedContent(
                    url=url,
                    success=False,
                    error=f"Extraction timed out after {self.timeout}s"
                )
                for url in urls
            ]
        except Exception as e:
            logger.error(f"Firecrawl batch extraction failed: {e}")
            return [
                ExtractedContent(
                    url=url,
                    success=False,
                    error=f"Batch extraction failed: {str(e)}"
                )
                for url in urls
            ]
    
    async def _run_batch_extraction(self, urls: List[str]) -> List[ExtractedContent]:
        """
        Run the actual batch extraction in a thread pool.
        
        This method handles the synchronous Firecrawl API calls in an async context.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._batch_scrape_sync, urls)
    
    def _batch_scrape_sync(self, urls: List[str]) -> List[ExtractedContent]:
        """
        Synchronous batch scraping using Firecrawl v1 batch_scrape_urls API.
        
        Args:
            urls: List of URLs to scrape.
            
        Returns:
            List of ExtractedContent objects.
        """
        results: List[ExtractedContent] = []
        
        try:
            params = {
                "scrapeOptions": {
                    "formats": ["markdown", "html"],
                    "includeTags": ["title", "meta"],
                    "excludeTags": ["script", "style", "nav", "footer", "header"],
                    "onlyMainContent": True,
                    "timeout": self.timeout * 1000  # ms
                }
            }
            logger.debug(f"Calling Firecrawl batch_scrape_urls with {len(urls)} URLs")
            response = self.client.batch_scrape_urls(urls=urls, params=params)
            
            if not response or 'data' not in response:
                logger.error("Invalid response from Firecrawl batch_scrape_urls API")
                return [
                    ExtractedContent(
                        url=url,
                        success=False,
                        error="Invalid API response"
                    )
                    for url in urls
                ]
            
            data_items = response.get('data', [])
            # Build index by sourceURL for quick lookup
            index_by_url: Dict[str, Dict[str, Any]] = {}
            for item in data_items:
                source_url = item.get('sourceURL') or item.get('url')
                if source_url:
                    index_by_url[str(source_url)] = item
            
            for url in urls:
                item = index_by_url.get(url)
                if not item:
                    results.append(
                        ExtractedContent(
                            url=url,
                            success=False,
                            error="URL not found in batch response"
                        )
                    )
                    continue
                results.append(self._process_scraped_item(url, item))
            
            successful = sum(1 for r in results if r.success)
            logger.info(f"Batch extraction completed: {successful}/{len(urls)} successful")
            return results
        except Exception as e:
            logger.error(f"Firecrawl batch_scrape_urls failed: {e}")
            return [
                ExtractedContent(
                    url=url,
                    success=False,
                    error=f"API error: {str(e)}"
                )
                for url in urls
            ]
    
    def _process_scraped_item(self, url: str, item: Dict[str, Any]) -> ExtractedContent:
        """
        Process a single scraped item from Firecrawl response.
        
        Args:
            url: The original URL that was scraped.
            item: The scraped data item from Firecrawl.
            
        Returns:
            ExtractedContent object with processed data.
        """
        try:
            if not item.get('success', True):
                error_msg = item.get('error', 'Unknown scraping error')
                return ExtractedContent(
                    url=url,
                    success=False,
                    error=error_msg
                )
            markdown = item.get('markdown', '')
            html = item.get('html', '')
            metadata = item.get('metadata', {})
            if not markdown and not html:
                return ExtractedContent(
                    url=url,
                    success=False,
                    error="No content extracted from page"
                )
            return ExtractedContent(
                url=url,
                markdown=markdown,
                html=html,
                metadata=metadata,
                success=True
            )
        except Exception as e:
            logger.error(f"Error processing scraped item for {url}: {e}")
            return ExtractedContent(
                url=url,
                success=False,
                error=f"Processing error: {str(e)}"
            )


# Global client instance
_firecrawl_client = None


def get_firecrawl_client() -> FirecrawlClient:
    """Get the global Firecrawl client instance."""
    global _firecrawl_client
    if _firecrawl_client is None:
        _firecrawl_client = FirecrawlClient()
    return _firecrawl_client


async def extract_urls_content(urls: List[str]) -> List[ExtractedContent]:
    """
    Convenience function to extract content from URLs using the global client.
    
    Args:
        urls: List of URLs to extract content from.
        
    Returns:
        List of ExtractedContent objects.
    """
    client = get_firecrawl_client()
    return await client.extract_batch(urls)