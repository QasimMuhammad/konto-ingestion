"""
Legal schema definitions for law sections and legal documents.
Handles tax laws, accounting laws, and other legal regulations.
"""

from typing import Optional
from pydantic import BaseModel, Field


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

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            # Add any custom encoders if needed
        }
