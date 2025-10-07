"""
Ingestion pipeline component for fetching data from sources.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

from .base_pipeline import BasePipeline, PipelineResult
from .source_loader import SourceLoader
from ..data_io import http_get, write_bronze_if_changed, log


class IngestionPipeline(BasePipeline):
    """Pipeline for ingesting data from external sources."""

    def __init__(
        self,
        pipeline_name: str,
        fetcher_func: Callable[[Dict[str, str], Path], Dict[str, Any]],
    ):
        super().__init__(pipeline_name)
        self.fetcher_func = fetcher_func
        self.source_loader: Optional[SourceLoader] = None
        self.bronze_dir: Optional[Path] = None

    def setup(self, sources_file: Path, bronze_dir: Path) -> None:
        """Setup the ingestion pipeline."""
        self.source_loader = SourceLoader(sources_file)
        self.bronze_dir = bronze_dir

    def filter_sources(
        self, filter_func: Callable[[List[Dict[str, str]]], List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Filter sources using the provided filter function."""
        if not self.source_loader:
            raise RuntimeError("Pipeline not setup. Call setup() first.")

        all_sources = self.source_loader.load_all_sources()
        return filter_func(all_sources)

    def ingest_source(self, source: Dict[str, str]) -> Dict[str, Any]:
        """Ingest a single source."""
        try:
            if self.bronze_dir is None:
                raise ValueError("Bronze directory not set")
            if self.result is None:
                raise ValueError("Pipeline not started - call start_execution first")

            result = self.fetcher_func(source, self.bronze_dir)

            if result.get("success", True) and "error" not in result:
                self.result.add_processed()
            else:
                self.result.add_error(
                    f"Failed to ingest {source.get('source_id', 'unknown')}: {result.get('error', 'Unknown error')}"
                )

            return result

        except Exception as e:
            error_msg = (
                f"Error ingesting {source.get('source_id', 'unknown')}: {str(e)}"
            )
            if self.result is not None:
                self.result.add_error(error_msg)
            return {
                "source_id": source.get("source_id", ""),
                "error": str(e),
                "success": False,
            }

    def save_metadata(self, results: List[Dict[str, Any]]) -> None:
        """Save ingestion metadata to bronze directory."""
        if not self.bronze_dir:
            return

        metadata_file = self.bronze_dir / "ingestion_metadata.json"
        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            log.info(f"Saved ingestion metadata to {metadata_file}")
        except Exception as e:
            log.error(f"Failed to save ingestion metadata: {e}")

    def execute(self) -> PipelineResult:
        """Execute the ingestion pipeline."""
        if not self.source_loader or not self.bronze_dir:
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

        self.result.total_items = len(sources)
        log.info(f"Found {len(sources)} sources to ingest")

        # Process each source
        results = []
        for source in sources:
            result = self.ingest_source(source)
            results.append(result)

        # Save metadata
        self.save_metadata(results)

        # Log summary
        successful = sum(
            1 for r in results if r.get("success", True) and "error" not in r
        )
        changed = sum(1 for r in results if r.get("changed", False))

        log.info(
            f"Ingestion complete: {successful}/{len(sources)} successful, {changed} files changed"
        )

        return self.result

    def get_sources_to_process(self) -> List[Dict[str, str]]:
        """Get sources to process. Override in subclasses."""
        return self.source_loader.load_all_sources() if self.source_loader else []


# Common fetcher functions for different source types


def fetch_html_source(source: Dict[str, str], bronze_dir: Path) -> Dict[str, Any]:
    """Fetch HTML content from a source URL."""
    source_id = source["source_id"]
    url = source["url"]
    file_path = bronze_dir / f"{source_id}.html"

    log.info(f"Ingesting {source_id} from {url}")

    try:
        content = http_get(url)
        write_result = write_bronze_if_changed(file_path, content)

        return {
            "source_id": source_id,
            "url": url,
            "file_path": str(file_path),
            "success": True,
            **write_result,
        }
    except Exception as e:
        log.error(f"Failed to ingest {source_id}: {e}")
        return {"source_id": source_id, "error": str(e), "success": False}


def fetch_pdf_source(source: Dict[str, str], bronze_dir: Path) -> Dict[str, Any]:
    """Fetch PDF content from a source URL."""
    source_id = source["source_id"]
    url = source["url"]
    file_path = bronze_dir / f"{source_id}.pdf"

    log.info(f"Ingesting {source_id} from {url}")

    try:
        content = http_get(url)
        write_result = write_bronze_if_changed(file_path, content)

        return {
            "source_id": source_id,
            "url": url,
            "file_path": str(file_path),
            "success": True,
            **write_result,
        }
    except Exception as e:
        log.error(f"Failed to ingest {source_id}: {e}")
        return {"source_id": source_id, "error": str(e), "success": False}
