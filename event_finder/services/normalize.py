import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime
from typing import Optional, Union
import dateutil.parser


def normalize_url(url: str) -> str:
    """
    Normalize URL by removing tracking parameters and converting to lowercase.
    
    Args:
        url: The URL to normalize
        
    Returns:
        Normalized URL string
    """
    if not url:
        return ""
    
    # Parse the URL
    parsed = urlparse(url.lower())
    
    # Tracking parameters to remove
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'msclkid', 'twclid', 'li_fat_id',
        '_ga', '_gid', '_gac', 'mc_cid', 'mc_eid',
        'ref', 'referrer', 'source', 'campaign'
    }
    
    # Parse query parameters
    query_params = parse_qs(parsed.query, keep_blank_values=False)
    
    # Remove tracking parameters
    filtered_params = {
        key: value for key, value in query_params.items() 
        if key.lower() not in tracking_params
    }
    
    # Sort parameters for consistent comparison
    sorted_params = dict(sorted(filtered_params.items()))
    
    # Rebuild query string
    new_query = urlencode(sorted_params, doseq=True) if sorted_params else ""
    
    # Rebuild URL
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip('/'),  # Remove trailing slash
        parsed.params,
        new_query,
        ""  # Remove fragment
    ))
    
    return normalized


def get_domain_from_url(url: str) -> str:
    """
    Extract domain (eTLD+1) from URL for deduplication.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Domain string (e.g., 'eventbrite.com')
    """
    if not url:
        return ""
    
    try:
        parsed = urlparse(url.lower())
        domain = parsed.netloc
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
    except Exception:
        return ""


def parse_date(date_str: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Parse date string into datetime object with multiple format support.
    
    Args:
        date_str: Date string, datetime object, or None
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not date_str:
        return None
        
    if isinstance(date_str, datetime):
        return date_str
        
    if not isinstance(date_str, str):
        return None
    
    # Clean the date string
    date_str = date_str.strip()
    if not date_str:
        return None
    
    try:
        # Use dateutil parser for flexible date parsing
        parsed_date = dateutil.parser.parse(date_str, fuzzy=True)
        return parsed_date
    except (ValueError, TypeError, dateutil.parser.ParserError):
        pass
    
    # Try common date patterns with regex
    date_patterns = [
        # ISO format: 2024-01-15, 2024/01/15
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        # US format: 01/15/2024, 1/15/24
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
        # European format: 15/01/2024, 15.01.2024
        r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                groups = match.groups()
                if len(groups) == 3:
                    # Try different interpretations based on pattern
                    if pattern.startswith(r'(\d{4})'):  # ISO format
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    elif pattern.startswith(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'):  # US format
                        month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                        if year < 100:  # Handle 2-digit years
                            year += 2000 if year < 50 else 1900
                    else:  # European format
                        day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        if year < 100:  # Handle 2-digit years
                            year += 2000 if year < 50 else 1900
                    
                    return datetime(year, month, day)
            except (ValueError, TypeError):
                continue
    
    return None


def normalize_event_name(name: str) -> str:
    """
    Normalize event name for deduplication comparison.
    
    Args:
        name: Event name to normalize
        
    Returns:
        Normalized event name
    """
    if not name:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()
    
    # Remove common prefixes/suffixes
    prefixes_to_remove = ['event:', 'webinar:', 'conference:', 'workshop:']
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove special characters for comparison
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    return normalized.strip()