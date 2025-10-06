"""
HTTP client utilities for fetching content from URLs.
Handles requests, headers, timeouts, and error handling.
"""

import logging
from typing import Optional
import requests

from .settings import settings

# Configure logging
log = logging.getLogger(__name__)


def http_get(url: str, timeout: Optional[int] = None) -> bytes:
    """Fetch content from URL with proper headers and error handling."""
    if timeout is None:
        timeout = settings.http_timeout

    headers = {"User-Agent": settings.user_agent}
    try:
        r = requests.get(url, timeout=timeout, headers=headers)
        r.raise_for_status()
        return r.content
    except requests.RequestException as e:
        log.error(f"Failed to fetch {url}: {e}")
        raise
