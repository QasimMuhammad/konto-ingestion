"""
HTTP client utilities for fetching content from URLs.
Handles requests, headers, timeouts, retries, and error handling.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logger import get_logger
from .settings import settings

logger = get_logger(__name__)


def create_session_with_retries(
    total_retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple[int, ...] = (500, 502, 503, 504),
) -> requests.Session:
    """
    Create requests session with retry logic.

    Args:
        total_retries: Total number of retries
        backoff_factor: Backoff factor for exponential delay (0.5s, 1s, 2s, ...)
        status_forcelist: HTTP status codes to retry on

    Returns:
        Configured requests session
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def http_get(
    url: str, timeout: int | None = None, max_retries: int = 3
) -> bytes:
    """
    Fetch content from URL with retry logic and proper error handling.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds (default from settings)
        max_retries: Maximum number of retries (default: 3)

    Returns:
        Response content as bytes

    Raises:
        requests.RequestException: If request fails after all retries
    """
    if timeout is None:
        timeout = settings.http_timeout

    headers = {"User-Agent": settings.user_agent}
    session = create_session_with_retries(total_retries=max_retries)

    try:
        response = session.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        logger.info(f"Successfully fetched {url}")
        return response.content
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url} after {max_retries} retries: {e}")
        raise
    finally:
        session.close()
