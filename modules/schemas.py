#!/usr/bin/env python3
"""
Compatibility layer for schemas module.
Re-exports schemas from focused schema modules for backward compatibility.
"""

# Import from focused schema modules
from .schemas.legal_schemas import LawSection
from .schemas.reporting_schemas import SpecNode, AmeldingRule
from .schemas.tax_schemas import VatRate
from .schemas.quality_schemas import QualityReport, SilverMetadata

# Re-export all schemas for backward compatibility
__all__ = [
    "LawSection",
    "SpecNode",
    "AmeldingRule",
    "VatRate",
    "QualityReport",
    "SilverMetadata",
]
