"""
Compatibility layer for data_io module.
Re-exports functions from the new focused modules for backward compatibility.
"""

# Import from new focused modules
from .http_client import http_get
from .hash_utils import sha256_bytes, compute_stable_hash
from .file_operations import write_bronze_if_changed, ensure_data_directories
from .logger import logger as log

# Re-export all functions for backward compatibility
__all__ = [
    "http_get",
    "sha256_bytes",
    "compute_stable_hash",
    "write_bronze_if_changed",
    "ensure_data_directories",
    "log",
]
