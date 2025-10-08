"""
Consolidated schema definitions for all data types.
Pydantic V2 models for Bronze, Silver, and Gold layers.
"""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class LawSection(BaseModel):
    """Law section schema for legal documents."""

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
    token_count: Optional[int] = Field(None, description="Token count for LLM")
    crawl_freq: Optional[str] = Field(None, description="Crawl frequency")

    model_config = ConfigDict(json_encoders={})


class VatRate(BaseModel):
    """VAT (MVA) rate schema."""

    rate_id: str
    rate_label: str
    rate_value: float
    description: str
    effective_from: str
    effective_to: Optional[str] = None
    source_url: str
    sha256: str
    domain: str
    source_type: str
    publisher: str
    jurisdiction: str = "NO"
    last_updated: Optional[str] = None
    token_count: Optional[int] = None
    crawl_freq: Optional[str] = None

    model_config = ConfigDict(json_encoders={})


class SpecNode(BaseModel):
    """SAF-T specification node schema."""

    node_id: str
    node_path: str
    node_label: str
    node_level: int
    parent_id: Optional[str] = None
    data_type: Optional[str] = None
    description: str
    cardinality: Optional[str] = None
    example_value: Optional[str] = None
    validation_rules: List[str] = Field(default_factory=list)
    technical_details: List[str] = Field(default_factory=list)
    source_url: str
    sha256: str
    domain: str = "accounting"
    source_type: str = "spec"
    publisher: str
    version: str = "1.3"
    jurisdiction: str = "NO"
    last_updated: Optional[str] = None
    token_count: Optional[int] = None
    crawl_freq: Optional[str] = None

    model_config = ConfigDict(json_encoders={})


class AmeldingRule(BaseModel):
    """A-melding (employee reporting) rule schema."""

    rule_id: str
    category: str
    subcategory: str
    field_id: str
    field_label: str
    description: str
    data_type: Optional[str] = None
    cardinality: Optional[str] = None
    validation_rules: List[str] = Field(default_factory=list)
    example_value: Optional[str] = None
    source_url: str
    sha256: str
    domain: str = "reporting"
    source_type: str = "spec"
    publisher: str
    version: str
    jurisdiction: str = "NO"
    last_updated: Optional[str] = None
    token_count: Optional[int] = None
    crawl_freq: Optional[str] = None

    model_config = ConfigDict(json_encoders={})


class QualityReport(BaseModel):
    """Quality assessment report schema."""

    overall_score: float
    completeness_score: float
    consistency_score: float
    accuracy_score: float
    timeliness_score: float
    total_records: int
    valid_records: int
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    assessment_date: str

    model_config = ConfigDict(json_encoders={})


class SilverMetadata(BaseModel):
    """Metadata for Silver layer dataset."""

    dataset_name: str
    version: str
    created_at: str
    total_files: int
    total_records: int
    domains: List[str]
    source_types: List[str]
    publishers: List[str]
    quality_score: float

    model_config = ConfigDict(json_encoders={})


__all__ = [
    "LawSection",
    "VatRate",
    "SpecNode",
    "AmeldingRule",
    "QualityReport",
    "SilverMetadata",
]
