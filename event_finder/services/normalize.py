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
        'srsltid'
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
    Parse date string into date object with multiple format support.
    
    Args:
        date_str: Date string, date object, or None
        
    Returns:
        Parsed date object or None if parsing fails
    """
    if not date_str:
        return None
        
    if isinstance(date_str, datetime):
        return date_str

    try:
        parsed_date = dateutil.parser.parse(date_str, fuzzy=True)
        return parsed_date
    except (ValueError, TypeError, dateutil.parser.ParserError):
        pass
    
    
    return None
