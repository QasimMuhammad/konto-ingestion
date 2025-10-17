"""
Hash utilities for content hashing and change detection.

Centralized hashing to ensure consistency across Bronze, Silver, and Gold layers.
All hashing uses SHA256 with UTF-8 encoding.
"""

import hashlib
import re


def sha256_bytes(content: bytes) -> str:
    """
    Generate SHA256 hash of bytes content.
    
    Used for: Bronze layer change detection, file integrity checks.
    """
    return hashlib.sha256(content).hexdigest()


def compute_stable_hash(text: str, canonicalize: bool = False) -> str:
    """
    Generate SHA256 hash of text content.
    
    Args:
        text: Text to hash
        canonicalize: If True, normalize whitespace and lowercase before hashing
                     (useful for content comparison ignoring formatting)
    
    Returns:
        SHA256 hash as hex string
    
    Canonicalization strategy (when enabled):
    - Lowercase
    - Strip leading/trailing whitespace
    - Collapse multiple spaces to single space
    - Preserves Norwegian characters (æ, ø, å)
    """
    if not text:
        return ""
    
    if canonicalize:
        canonical = text.lower().strip()
        canonical = re.sub(r"\s+", " ", canonical)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
