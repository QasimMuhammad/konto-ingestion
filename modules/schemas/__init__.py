"""
Schema modules for Silver layer data validation.
Provides focused, domain-specific Pydantic schemas.
"""

# Re-export all schemas for backward compatibility
from .legal_schemas import LawSection
from .reporting_schemas import SpecNode, AmeldingRule
from .tax_schemas import VatRate
from .quality_schemas import QualityReport, SilverMetadata

__all__ = [
    "LawSection",
    "SpecNode",
    "AmeldingRule",
    "VatRate",
    "QualityReport",
    "SilverMetadata",
]
