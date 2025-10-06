"""
Quality and metadata schema definitions.
Handles quality reports, processing statistics, and metadata.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class QualityReport(BaseModel):
    """Quality report schema for processing statistics."""

    # Make fields optional to match existing data structure
    total_files: Optional[int] = Field(
        None, description="Total number of files processed"
    )
    valid_files: Optional[int] = Field(None, description="Number of valid files")
    invalid_files: Optional[int] = Field(None, description="Number of invalid files")
    success_rate: Optional[float] = Field(None, description="Success rate percentage")
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    file_details: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed file information"
    )
    errors: Optional[Dict[str, Any]] = Field(None, description="Error details")
    last_updated: Optional[str] = Field(None, description="Last updated timestamp")

    # Add fields that exist in current data
    total_processed: Optional[int] = Field(None, description="Total processed records")
    domains: Optional[Dict[str, Any]] = Field(
        None, description="Record counts by domain"
    )
    sources: Optional[Dict[str, Any]] = Field(
        None, description="Record counts by source"
    )
    publishers: Optional[Dict[str, Any]] = Field(
        None, description="Record counts by publisher"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            # Add any custom encoders if needed
        }


class SilverMetadata(BaseModel):
    """Silver layer metadata schema."""

    layer: str = Field(default="silver", description="Data layer")
    version: str = Field(..., description="Schema version")
    created_at: str = Field(..., description="Creation timestamp")
    last_updated: str = Field(..., description="Last updated timestamp")
    total_records: int = Field(..., description="Total number of records")
    domains: Dict[str, int] = Field(
        default_factory=dict, description="Record counts by domain"
    )
    sources: Dict[str, int] = Field(
        default_factory=dict, description="Record counts by source"
    )
    publishers: Dict[str, int] = Field(
        default_factory=dict, description="Record counts by publisher"
    )
    quality_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Quality metrics"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            # Add any custom encoders if needed
        }
