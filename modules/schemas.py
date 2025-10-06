#!/usr/bin/env python3
"""
Pydantic schemas for Silver layer data validation.
Defines data models and validation rules for all Silver entities.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class LawSection(BaseModel):
    """Law section schema."""

    law_id: str = Field(..., description="Unique identifier for the law")
    section_id: str = Field(..., description="Section identifier (e.g., PARAGRAF_1-1)")
    section_label: str = Field(
        ..., description="Human-readable section label (e.g., § 1-1)"
    )
    path: str = Field(
        ..., description="Full path to section (e.g., Kapittel 1 PARAGRAF_1-1)"
    )
    heading: str = Field(..., description="Section heading")
    text_plain: str = Field(..., description="Cleaned plain text content")
    source_url: str = Field(..., description="Source URL")
    sha256: str = Field(..., description="Content hash")
    domain: str = Field(..., description="Domain (tax, accounting, reporting)")
    source_type: str = Field(..., description="Source type (law, forskrift, spec)")
    publisher: str = Field(..., description="Publisher (Lovdata, Skatteetaten, etc.)")
    version: str = Field(..., description="Version identifier")
    jurisdiction: str = Field(..., description="Jurisdiction (NO, EU, etc.)")
    effective_from: Optional[str] = Field(None, description="Effective from date")
    effective_to: Optional[str] = Field(None, description="Effective to date")
    law_title: str = Field(..., description="Full law title")
    chapter: str = Field(..., description="Chapter name")
    chapter_no: str = Field(..., description="Chapter number")
    section_no: Optional[str] = Field(None, description="Section number")
    subsection_no: Optional[str] = Field(None, description="Subsection number")
    paragraph_no: Optional[str] = Field(None, description="Paragraph number")
    text_length: Optional[int] = Field(None, description="Text length in characters")
    word_count: Optional[int] = Field(None, description="Word count")
    has_citations: Optional[bool] = Field(
        None, description="Whether section contains citations"
    )
    has_amendments: Optional[bool] = Field(
        None, description="Whether section has amendments"
    )
    is_current: Optional[bool] = Field(
        None, description="Whether section is currently in force"
    )
    last_updated: Optional[str] = Field(None, description="Last updated timestamp")
    processing_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Processing metadata"
    )

    @validator("domain")
    def validate_domain(cls, v):
        allowed_domains = ["tax", "accounting", "reporting"]
        if v not in allowed_domains:
            raise ValueError(f"Domain must be one of {allowed_domains}")
        return v

    @validator("source_type")
    def validate_source_type(cls, v):
        allowed_types = ["law", "forskrift", "spec", "guidance", "form", "rates"]
        if v not in allowed_types:
            raise ValueError(f"Source type must be one of {allowed_types}")
        return v

    @validator("jurisdiction")
    def validate_jurisdiction(cls, v):
        allowed_jurisdictions = ["NO", "EU", "US", "UK"]
        if v not in allowed_jurisdictions:
            raise ValueError(f"Jurisdiction must be one of {allowed_jurisdictions}")
        return v


class SpecNode(BaseModel):
    """SAF-T specification node schema."""

    spec: str = Field(..., description="Specification name (e.g., SAF-T)")
    version: str = Field(..., description="Specification version")
    node_path: str = Field(..., description="Node path in specification")
    cardinality: str = Field(..., description="Cardinality (e.g., 0..1, 1..*, 0..*)")
    description: str = Field(..., description="Node description")
    source_url: str = Field(..., description="Source URL")
    sha256: str = Field(..., description="Content hash")
    domain: str = Field(default="reporting", description="Domain")
    source_type: str = Field(default="spec", description="Source type")
    publisher: str = Field(..., description="Publisher")
    jurisdiction: str = Field(default="NO", description="Jurisdiction")
    is_current: bool = Field(..., description="Whether node is currently valid")
    effective_from: Optional[str] = Field(None, description="Effective from date")
    effective_to: Optional[str] = Field(None, description="Effective to date")
    priority: str = Field(default="medium", description="Priority level")
    complexity: str = Field(default="medium", description="Complexity level")
    data_type: str = Field(default="string", description="Data type")
    format: str = Field(default="XML", description="Data format")
    validation_rules: List[str] = Field(
        default_factory=list, description="Validation rules"
    )
    business_rules: List[str] = Field(
        default_factory=list, description="Business rules"
    )
    examples: List[str] = Field(default_factory=list, description="Usage examples")
    dependencies: List[str] = Field(
        default_factory=list, description="Dependencies"
    )
    technical_details: List[str] = Field(
        default_factory=list, description="Technical details"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    last_updated: str = Field(..., description="Last updated timestamp")

    @validator("cardinality")
    def validate_cardinality(cls, v):
        # Allow common cardinality patterns
        import re

        if not re.match(r"^\d+\.\.\d*$", v) and v not in [
            "0..1",
            "1..1",
            "0..*",
            "1..*",
        ]:
            # If it doesn't match standard pattern, try to normalize
            if v.lower() in ["optional", "valgfri"]:
                return "0..1"
            elif v.lower() in ["required", "obligatorisk", "mandatory"]:
                return "1..1"
            elif v.lower() in ["multiple", "flere", "many"]:
                return "0..*"
            elif v.lower() in ["one or more", "en eller flere"]:
                return "1..*"
        return v


class VatRate(BaseModel):
    """VAT rate schema."""

    kind: str = Field(..., description="Rate kind (standard, reduced, zero, high)")
    value: str = Field(..., description="Rate value (e.g., 25%, 15%)")
    percentage: float = Field(..., description="Rate as percentage")
    valid_from: Optional[str] = Field(None, description="Valid from date")
    valid_to: Optional[str] = Field(None, description="Valid to date")
    description: str = Field(..., description="Rate description")
    source_url: str = Field(..., description="Source URL")
    sha256: str = Field(..., description="Content hash")
    domain: str = Field(default="tax", description="Domain")
    source_type: str = Field(default="rates", description="Source type")
    publisher: str = Field(..., description="Publisher")
    jurisdiction: str = Field(default="NO", description="Jurisdiction")
    is_current: bool = Field(..., description="Whether rate is currently valid")
    category: str = Field(..., description="Detailed category (food_products, water_services, etc.)")
    applies_to: List[str] = Field(
        default_factory=list, description="What this rate applies to"
    )
    exceptions: List[str] = Field(
        default_factory=list, description="Exceptions to this rate"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    last_updated: str = Field(..., description="Last updated timestamp")

    @validator("kind")
    def validate_kind(cls, v):
        allowed_kinds = ["standard", "reduced", "zero", "high", "mva"]
        if v not in allowed_kinds:
            raise ValueError(f"Kind must be one of {allowed_kinds}")
        return v

    @validator("percentage")
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v

    @validator("value")
    def validate_value(cls, v):
        import re

        if not re.match(r"^\d+[,\s]*\d*%$", v):
            raise ValueError('Value must be in format like "25%" or "15,5%"')
        return v


class QualityReport(BaseModel):
    """Quality report schema."""

    total_processed: int = Field(..., description="Total items processed")
    total_saved: int = Field(..., description="Total items saved")
    rejected_short_text: int = Field(..., description="Items rejected for short text")
    validation_issues: int = Field(..., description="Validation issues found")
    total_tokens: int = Field(..., description="Total tokens processed")
    domains: Dict[str, Dict[str, int]] = Field(..., description="Statistics by domain")
    source_types: Dict[str, int] = Field(..., description="Statistics by source type")
    publishers: Dict[str, int] = Field(..., description="Statistics by publisher")
    processing_time_seconds: Optional[float] = Field(
        None, description="Total processing time"
    )
    average_text_length: Optional[float] = Field(
        None, description="Average text length"
    )
    average_word_count: Optional[float] = Field(None, description="Average word count")
    error_rate: Optional[float] = Field(None, description="Error rate (0-1)")
    success_rate: Optional[float] = Field(None, description="Success rate (0-1)")
    last_updated: Optional[str] = Field(None, description="Last updated timestamp")

    @validator("error_rate", "success_rate")
    def validate_rates(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Rate must be between 0 and 1")
        return v


class AmeldingRule(BaseModel):
    """A-meldingen rule schema."""

    rule_id: str = Field(..., description="Unique rule identifier")
    title: str = Field(..., description="Rule title")
    description: str = Field(..., description="Rule description")
    category: str = Field(..., description="Rule category")
    applies_to: List[str] = Field(..., description="Who this rule applies to")
    requirements: List[str] = Field(..., description="Specific requirements")
    examples: List[str] = Field(..., description="Usage examples")
    source_url: str = Field(..., description="Source URL")
    sha256: str = Field(..., description="Content hash")
    domain: str = Field(default="reporting", description="Domain")
    source_type: str = Field(..., description="Source type")
    publisher: str = Field(..., description="Publisher")
    jurisdiction: str = Field(default="NO", description="Jurisdiction")
    is_current: bool = Field(..., description="Whether rule is currently valid")
    effective_from: Optional[str] = Field(None, description="Effective from date")
    effective_to: Optional[str] = Field(None, description="Effective to date")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    complexity: str = Field(..., description="Complexity level (high, medium, low)")
    technical_details: List[str] = Field(
        default_factory=list, description="Technical details"
    )
    validation_rules: List[str] = Field(
        default_factory=list, description="Validation rules"
    )
    field_mappings: Dict[str, str] = Field(
        default_factory=dict, description="Field mappings"
    )
    business_rules: List[str] = Field(
        default_factory=list, description="Business rules"
    )
    last_updated: str = Field(..., description="Last updated timestamp")

    @validator("category")
    def validate_category(cls, v):
        allowed_categories = [
            "salary_reporting",
            "tax_deductions", 
            "employer_obligations",
            "submission_deadlines",
            "form_guidance",
            "general_guidance"
        ]
        if v not in allowed_categories:
            raise ValueError(f"Category must be one of {allowed_categories}")
        return v

    @validator("priority", "complexity")
    def validate_levels(cls, v):
        allowed_levels = ["high", "medium", "low"]
        if v not in allowed_levels:
            raise ValueError(f"Level must be one of {allowed_levels}")
        return v


class SilverMetadata(BaseModel):
    """Metadata for Silver layer files."""

    file_name: str = Field(..., description="File name")
    file_path: str = Field(..., description="File path")
    file_size_bytes: int = Field(..., description="File size in bytes")
    record_count: int = Field(..., description="Number of records")
    schema_version: str = Field(..., description="Schema version")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    source_files: List[str] = Field(..., description="Source Bronze files")
    validation_status: str = Field(..., description="Validation status")
    validation_errors: List[str] = Field(
        default_factory=list, description="Validation errors"
    )
    processing_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Processing metadata"
    )


# Export schemas for easy import
__all__ = ["LawSection", "SpecNode", "VatRate", "AmeldingRule", "QualityReport", "SilverMetadata"]
