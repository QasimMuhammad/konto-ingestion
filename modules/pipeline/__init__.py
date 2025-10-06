"""
Pipeline abstraction components for data processing.
Provides reusable components for common pipeline patterns.
"""

from .base_pipeline import BasePipeline, PipelineResult
from .ingestion_pipeline import IngestionPipeline
from .processing_pipeline import ProcessingPipeline
from .source_loader import SourceLoader

__all__ = [
    "BasePipeline",
    "PipelineResult", 
    "IngestionPipeline",
    "ProcessingPipeline",
    "SourceLoader"
]
