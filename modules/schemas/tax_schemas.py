"""
Tax schema definitions for VAT rates and tax-related data.
Handles Norwegian VAT rates, tax calculations, and tax regulations.
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field


class VatRate(BaseModel):
    """VAT rate schema for Norwegian tax rates."""

    kind: str = Field(..., description="Rate kind (standard, reduced, zero, etc.)")
    percentage: float = Field(..., description="VAT percentage rate")
    description: str = Field(..., description="Human-readable description")
    category: str = Field(..., description="Rate category")
    applies_to: List[str] = Field(
        default_factory=list, description="What this rate applies to"
    )
    exceptions: List[str] = Field(
        default_factory=list, description="Exceptions to this rate"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    source_url: str = Field(..., description="Source URL")
    sha256: str = Field(..., description="Content hash")
    publisher: str = Field(..., description="Publisher (Skatteetaten, etc.)")
    jurisdiction: str = Field(default="NO", description="Jurisdiction")
    is_current: bool = Field(
        default=True, description="Whether rate is currently in effect"
    )
    last_updated: str = Field(..., description="Last updated timestamp")

    class Config:
        """Pydantic configuration."""

        json_encoders: dict[type, Any] = {
            # Add any custom encoders if needed
        }
