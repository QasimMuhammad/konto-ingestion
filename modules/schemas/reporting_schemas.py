"""
Reporting schema definitions for SAF-T and A-meldingen.
Handles technical specifications, business rules, and reporting requirements.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SpecNode(BaseModel):
    """SAF-T specification node schema."""

    node_path: str = Field(..., description="Full path to the node")
    cardinality: str = Field(..., description="Cardinality (1..1, 0..*, etc.)")
    description: str = Field(..., description="Node description")
    source_url: str = Field(..., description="Source URL")
    sha256: str = Field(..., description="Content hash")
    domain: str = Field(default="reporting", description="Domain")
    source_type: str = Field(default="spec", description="Source type")
    publisher: str = Field(..., description="Publisher")
    jurisdiction: str = Field(default="NO", description="Jurisdiction")
    is_current: bool = Field(
        default=True, description="Whether specification is current"
    )
    effective_from: Optional[str] = Field(None, description="Effective from date")
    effective_to: Optional[str] = Field(None, description="Effective to date")
    priority: Optional[str] = Field(None, description="Priority level")
    complexity: Optional[str] = Field(None, description="Complexity level")
    data_type: str = Field(default="string", description="Data type")
    format: Optional[str] = Field(None, description="Format specification")
    validation_rules: List[str] = Field(
        default_factory=list, description="Validation rules"
    )
    business_rules: List[str] = Field(
        default_factory=list, description="Business rules"
    )
    dependencies: List[str] = Field(default_factory=list, description="Dependencies")
    technical_details: Optional[str | List[str]] = Field(
        None, description="Technical details"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    last_updated: str = Field(..., description="Last updated timestamp")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            # Add any custom encoders if needed
        }


class AmeldingRule(BaseModel):
    """A-meldingen business rule schema."""

    rule_id: str = Field(..., description="Unique rule identifier")
    title: str = Field(..., description="Rule title")
    description: str = Field(..., description="Rule description")
    category: str = Field(..., description="Rule category")
    source_url: str = Field(..., description="Source URL")
    sha256: str = Field(..., description="Content hash")
    domain: str = Field(default="reporting", description="Domain")
    source_type: str = Field(default="guidance", description="Source type")
    publisher: str = Field(..., description="Publisher")
    jurisdiction: str = Field(default="NO", description="Jurisdiction")
    is_current: bool = Field(default=True, description="Whether rule is current")
    effective_from: Optional[str] = Field(None, description="Effective from date")
    effective_to: Optional[str] = Field(None, description="Effective to date")
    priority: Optional[str] = Field(None, description="Priority level")
    complexity: Optional[str] = Field(None, description="Complexity level")
    technical_details: Optional[str | List[str]] = Field(
        None, description="Technical details"
    )
    validation_rules: List[str] = Field(
        default_factory=list, description="Validation rules"
    )
    field_mappings: Dict[str, Any] = Field(
        default_factory=dict, description="Field mappings"
    )
    business_rules: List[str] = Field(
        default_factory=list, description="Business rules"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    last_updated: str = Field(..., description="Last updated timestamp")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            # Add any custom encoders if needed
        }
