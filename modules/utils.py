import hashlib
import logging
from pathlib import Path
from typing import Dict, Any
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def sha256_bytes(content: bytes) -> str:
    """Generate SHA256 hash of bytes content."""
    return hashlib.sha256(content).hexdigest()


def http_get(url: str, timeout: int = None) -> bytes:
    """Fetch content from URL with proper headers and error handling."""
    # Import here to avoid circular imports
    from .config import settings

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


def write_bronze_if_changed(path: Path, content: bytes) -> Dict[str, Any]:
    """Write content to Bronze layer only if it has changed (idempotent)."""
    h = sha256_bytes(content)
    old_content = path.read_bytes() if path.exists() else None

    if not old_content or sha256_bytes(old_content) != h:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        changed = True
        log.info(f"Wrote new content to {path}")
    else:
        changed = False
        log.info(f"Content unchanged, skipping {path}")

    return {
        "sha256": h,
        "changed": changed,
        "size_bytes": len(content),
        "timestamp": datetime.now().isoformat(),
    }


def ensure_data_directories(base_path: Path) -> Dict[str, Path]:
    """Ensure Bronze, Silver, and Gold directories exist."""
    bronze = base_path / "bronze"
    silver = base_path / "silver"
    gold = base_path / "gold"

    for directory in [bronze, silver, gold]:
        directory.mkdir(parents=True, exist_ok=True)

    return {"bronze": bronze, "silver": silver, "gold": gold}
