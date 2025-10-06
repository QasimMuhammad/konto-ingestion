"""
Hash utilities for content hashing and change detection.
Provides SHA256 hashing for bytes and text content.
"""

import hashlib


def sha256_bytes(content: bytes) -> str:
    """Generate SHA256 hash of bytes content."""
    return hashlib.sha256(content).hexdigest()


def compute_stable_hash(content: str) -> str:
    """Generate stable hash for text content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
