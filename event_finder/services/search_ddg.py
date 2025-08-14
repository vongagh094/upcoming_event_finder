"""
DuckDuckGo search service for finding event-related content.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import logging
from urllib.parse import quote_plus

from event_finder.config.lists import EXCLUDE_DOMAINS, DDG_TEMPLATES
from event_finder.services.normalize import get_domain_from_url
from event_finder.config.settings import DDG_TIMEOUT

logger = logging.getLogger(__name__)


def search_duckduckgo(speaker_name: str, max_results: int = 20) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo for events related to the given speaker.
    
    Args:
        speaker_name: Name of the speaker to search for
        max_results: Maximum number of results to return
        
    Returns:
        List of search results with title, url, snippet, and source
    """
    if not speaker_name or not speaker_name.strip():
        logger.warning("Empty speaker name provided")
        return []
    
    all_results = []
    
    # Generate search queries using templates
    queries = _build_search_queries(speaker_name)
    logger.info(f"Generated {len(queries)} search queries for speaker: {speaker_name}")
    
    successful_queries = 0
    for i, query in enumerate(queries):
        try:
            logger.debug(f"Executing query {i+1}/{len(queries)}: {query}")
            results = _perform_ddg_search(query)
            
            if results:
                filtered_results = _filter_results(results)
                all_results.extend(filtered_results)
                successful_queries += 1
                logger.debug(f"Query returned {len(filtered_results)} filtered results")
            else:
                logger.debug(f"Query returned no results")
            
            # Add small delay between requests to be respectful
            time.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed for query '{query}': {e}")
            continue
    
    logger.info(f"Completed {successful_queries}/{len(queries)} successful queries")
    
    # Remove duplicates and limit results
    unique_results = _deduplicate_results(all_results)
    final_results = unique_results[:max_results]
    
    logger.info(f"Returning {len(final_results)} unique results after deduplication")
    return final_results


def _build_search_queries(speaker_name: str) -> List[str]:
    """
    Build search queries using templates and speaker name.
    
    Args:
        speaker_name: Name of the speaker
        
    Returns:
        List of search query strings
    """
    queries = []
    
    for template in DDG_TEMPLATES:
        query = template.format(speaker_name)
        queries.append(query)
    
    return queries


def _perform_ddg_search(query: str) -> List[Dict[str, str]]:
    """
    Perform a single DuckDuckGo search and parse results.
    
    Args:
        query: Search query string
        
    Returns:
        List of raw search results
    """
    # DuckDuckGo search URL
    encoded_query = quote_plus(query)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=DDG_TIMEOUT)
        
        # Log response details for debugging
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        logger.debug(f"Response content length: {len(response.content)}")
        
        # Check if we got a valid response
        if response.status_code == 202:
            logger.warning(f"DuckDuckGo returned 202 (rate limited or blocked) for query: {query}")
            return []
        
        response.raise_for_status()
        
        # Check if we actually got content
        if not response.text or len(response.text) < 100:
            logger.warning(f"DuckDuckGo returned empty or minimal content for query: {query}")
            return []
        
        return _parse_ddg_html(response.text)
        
    except requests.RequestException as e:
        logger.error(f"Request failed for query '{query}': {e}")
        return []


def _parse_ddg_html(html_content: str) -> List[Dict[str, str]]:
    """
    Parse DuckDuckGo HTML response to extract search results.
    
    Args:
        html_content: HTML content from DuckDuckGo
        
    Returns:
        List of parsed search results
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # Find search result containers - DuckDuckGo uses various selectors
    result_selectors = [
        'div.result',
        'div.web-result', 
        'div[class*="result"]',
        'div.results_links',
        'div.result__body',
        'article[data-testid="result"]',
        '.result',
        '[data-testid="result"]'
    ]
    
    result_elements = []
    for selector in result_selectors:
        result_elements = soup.select(selector)
        if result_elements:
            logger.debug(f"Found {len(result_elements)} results using selector: {selector}")
            break
    
    if not result_elements:
        # Try to find any links that might be results
        logger.debug("No standard result containers found, looking for links")
        all_links = soup.find_all('a', href=True)
        logger.debug(f"Found {len(all_links)} total links")
        
        # Filter for links that look like search results
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Skip internal DuckDuckGo links and empty links
            if (href.startswith('http') and 
                text and 
                len(text) > 10 and
                'duckduckgo.com' not in href):
                
                results.append({
                    'title': text,
                    'url': href,
                    'snippet': '',
                    'source': 'duckduckgo'
                })
    else:
        for element in result_elements:
            try:
                result = _extract_result_data(element)
                if result:
                    results.append(result)
            except Exception as e:
                logger.debug(f"Failed to parse result element: {e}")
                continue
    
    logger.debug(f"Parsed {len(results)} results from HTML")
    return results


def _extract_result_data(element) -> Optional[Dict[str, str]]:
    """
    Extract title, URL, and snippet from a search result element.
    
    Args:
        element: BeautifulSoup element containing search result
        
    Returns:
        Dictionary with result data or None if extraction fails
    """
    # Try multiple selectors for title and URL
    title_selectors = [
        'a.result__a',
        'h2 a', 
        '.result__title a',
        'a[class*="title"]',
        'h3 a',
        'a[data-testid="result-title-a"]',
        '.result-title a',
        'a'  # fallback to any link
    ]
    
    title_element = None
    for selector in title_selectors:
        title_element = element.select_one(selector)
        if title_element:
            break
    
    if not title_element:
        return None
    
    title = title_element.get_text(strip=True)
    url = title_element.get('href')
    
    if not title or not url:
        return None
    
    # Clean up URL (DuckDuckGo sometimes uses redirect URLs)
    if url.startswith('/l/?uddg='):
        # Extract actual URL from DuckDuckGo redirect
        try:
            from urllib.parse import unquote
            url = unquote(url.split('uddg=')[1])
        except:
            pass
    elif url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/'):
        # Relative URL, skip it
        return None
    
    # Try to find snippet/description
    snippet_selectors = [
        '.result__snippet',
        '.result-snippet', 
        '.snippet',
        'span.result__snippet',
        '.result-desc',
        '[data-testid="result-snippet"]',
        'p'  # fallback to any paragraph
    ]
    
    snippet = ""
    for selector in snippet_selectors:
        snippet_element = element.select_one(selector)
        if snippet_element:
            snippet = snippet_element.get_text(strip=True)
            break
    
    return {
        'title': title,
        'url': url,
        'snippet': snippet,
        'source': 'duckduckgo'
    }


def _filter_results(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter out results from excluded domains.
    
    Args:
        results: List of search results
        
    Returns:
        Filtered list of results
    """
    filtered = []
    
    for result in results:
        url = result.get('url', '')
        if not url:
            continue
            
        domain = get_domain_from_url(url)
        
        # Skip if domain is in exclude list
        if domain in EXCLUDE_DOMAINS:
            logger.debug(f"Filtering out excluded domain: {domain}")
            continue
            
        # Skip if URL doesn't look valid
        if not url.startswith(('http://', 'https://')):
            continue
            
        filtered.append(result)
    
    return filtered


def _deduplicate_results(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Remove duplicate results based on URL.
    
    Args:
        results: List of search results
        
    Returns:
        Deduplicated list of results
    """
    seen_urls = set()
    unique_results = []
    
    for result in results:
        url = result.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)
    
    return unique_results