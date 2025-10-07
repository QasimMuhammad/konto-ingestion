"""
Processing pipeline component for transforming data between layers.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

from .base_pipeline import BasePipeline, PipelineResult
from .source_loader import SourceLoader
from ..data_io import log


class ProcessingPipeline(BasePipeline):
    """Pipeline for processing data between Bronze, Silver, and Gold layers."""

    def __init__(
        self,
        pipeline_name: str,
        processor_func: Callable[[List[Dict[str, str]], Path, Path], Dict[str, Any]],
    ):
        super().__init__(pipeline_name)
        self.processor_func = processor_func
        self.source_loader: Optional[SourceLoader] = None
        self.bronze_dir: Optional[Path] = None
        self.silver_dir: Optional[Path] = None

    def setup(self, sources_file: Path, bronze_dir: Path, silver_dir: Path) -> None:
        """Setup the processing pipeline."""
        self.source_loader = SourceLoader(sources_file)
        self.bronze_dir = bronze_dir
        self.silver_dir = silver_dir

    def filter_sources(
        self, filter_func: Callable[[List[Dict[str, str]]], List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Filter sources using the provided filter function."""
        if not self.source_loader:
            raise RuntimeError("Pipeline not setup. Call setup() first.")

        all_sources = self.source_loader.load_all_sources()
        return filter_func(all_sources)

    def process_sources(self, sources: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process sources using the processor function."""
        try:
            if self.bronze_dir is None or self.silver_dir is None:
                raise ValueError("Bronze or Silver directory not set")
            if self.result is None:
                raise ValueError("Pipeline not started - call start_execution first")

            stats = self.processor_func(sources, self.bronze_dir, self.silver_dir)

            # Update result based on stats
            if isinstance(stats, dict):
                self.result.total_items = stats.get("total_sources", len(sources))
                self.result.processed_items = stats.get("processed_sources", 0)
                self.result.failed_items = stats.get(
                    "total_sources", len(sources)
                ) - stats.get("processed_sources", 0)

                if "errors" in stats:
                    for error in stats["errors"]:
                        self.result.add_error(error)

                # Store additional stats in metadata
                for key, value in stats.items():
                    if key not in ["total_sources", "processed_sources", "errors"]:
                        self.result.metadata[key] = value

            return stats

        except Exception as e:
            error_msg = f"Error processing sources: {str(e)}"
            if self.result is not None:
                self.result.add_error(error_msg)
            return {"error": error_msg}

    def save_results(self, output_file: str, data: List[Dict[str, Any]]) -> None:
        """Save processing results to silver directory."""
        if not self.silver_dir:
            return

        output_path = self.silver_dir / output_file
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.info(f"Saved {len(data)} items to {output_path}")
        except Exception as e:
            log.error(f"Failed to save results to {output_path}: {e}")
            if self.result is not None:
                self.result.add_error(f"Failed to save results: {e}")

    def execute(self) -> PipelineResult:
        """Execute the processing pipeline."""
        if not self.source_loader or not self.bronze_dir or not self.silver_dir:
            raise RuntimeError("Pipeline not setup. Call setup() first.")

        # Start execution and initialize result
        self.start_execution()
        assert self.result is not None, (
            "Result should be initialized after start_execution"
        )

        # Get sources to process (to be implemented by subclasses)
        sources = self.get_sources_to_process()

        if not sources:
            log.error(f"No sources found for {self.pipeline_name}")
            self.result.add_error("No sources found")
            return self.result

        log.info(f"Found {len(sources)} sources to process")

        # Process sources
        self.process_sources(sources)

        # Log summary
        self.print_summary(f"{self.pipeline_name} PROCESSING", "sources")

        return self.result

    def get_sources_to_process(self) -> List[Dict[str, str]]:
        """Get sources to process. Override in subclasses."""
        return self.source_loader.load_all_sources() if self.source_loader else []


# Common processor functions for different data types


def process_lovdata_sources(
    sources: List[Dict[str, str]], bronze_dir: Path, silver_dir: Path
) -> Dict[str, Any]:
    """Process Lovdata sources from Bronze to Silver."""
    from ..parsers.lovdata_parser import parse_lovdata_html
    from ..cleaners.legal_text_cleaner import (
        clean_legal_text,
        normalize_text,
    )

    stats: dict[str, Any] = {
        "total_sources": len(sources),
        "processed_sources": 0,
        "total_sections": 0,
        "errors": [],
    }

    all_sections: list[Any] = []

    for source in sources:
        source_id = source["source_id"]
        file_path = bronze_dir / f"{source_id}.html"

        if not file_path.exists():
            stats["errors"].append(f"Bronze file not found: {file_path}")
            continue

        try:
            # Parse HTML content
            html_content = file_path.read_text(encoding="utf-8")
            sections = parse_lovdata_html(
                html_content, source_id, source["url"], "bronze_hash"
            )

            # Clean and normalize sections
            cleaned_sections = []
            for section in sections:
                # Convert dataclass to dictionary
                section_dict: dict[str, Any] = {
                    "law_id": section.law_id,
                    "section_id": section.section_id,
                    "path": section.path,
                    "heading": section.heading,
                    "text_plain": section.text_plain,
                    "source_url": section.source_url,
                    "sha256": section.sha256,
                }

                # Add source metadata
                section_dict.update(
                    {
                        "domain": source.get("domain", ""),
                        "source_type": source.get("source_type", ""),
                        "publisher": source.get("publisher", ""),
                        "is_current": True,
                        "last_updated": "2024-01-01T00:00:00Z",
                    }
                )

                # Clean text content
                section_dict["text_plain"] = clean_legal_text(
                    section_dict["text_plain"]
                )
                section_dict["text_plain"] = normalize_text(section_dict["text_plain"])

                cleaned_sections.append(section_dict)

            all_sections.extend(cleaned_sections)
            stats["processed_sources"] += 1
            stats["total_sections"] += len(cleaned_sections)

            log.info(f"Processed {source_id}: {len(cleaned_sections)} sections")

        except Exception as e:
            error_msg = f"Error processing {source_id}: {str(e)}"
            stats["errors"].append(error_msg)
            log.error(error_msg)

    # Save to silver layer
    if all_sections:
        output_file = silver_dir / "law_sections.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_sections, f, indent=2, ensure_ascii=False)
        log.info(f"Saved {len(all_sections)} sections to {output_file}")

    return stats
