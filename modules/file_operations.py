"""
File operations utilities for Bronze, Silver, and Gold layers.
Handles idempotent writes, directory management, and content tracking.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .hash_utils import sha256_bytes

# Configure logging
log = logging.getLogger(__name__)


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


def ensure_data_directories(base_path: Path = None) -> Dict[str, Path]:
    """Ensure Bronze, Silver, and Gold directories exist."""
    if base_path is None:
        base_path = Path(__file__).parent.parent / "data"

    bronze = base_path / "bronze"
    silver = base_path / "silver"
    gold = base_path / "gold"

    for directory in [bronze, silver, gold]:
        directory.mkdir(parents=True, exist_ok=True)

    return {"bronze": bronze, "silver": silver, "gold": gold}
