#!/usr/bin/env python3
"""
Accounting regulations ingestion script.
Fetches and stores Norwegian accounting laws and SAF-T specifications.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

from modules.utils import (
    http_get,
    write_bronze_if_changed,
    ensure_data_directories,
    log,
)


def load_sources(
    sources_path: Path, domain: str = "accounting"
) -> List[Dict[str, str]]:
    """Load sources from CSV file, filtered by domain."""
    sources = []
    with open(sources_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter by domain if specified
            if not domain or row.get("domain", "").lower() == domain.lower():
                sources.append(row)
    return sources


def ingest_accounting_regulation(
    source: Dict[str, str], bronze_dir: Path
) -> Dict[str, Any]:
    """Ingest a single accounting regulation source."""
    source_id = source["source_id"]
    url = source["url"]

    log.info(f"Processing {source_id}: {source['title']}")

    try:
        # Fetch content
        raw_content = http_get(url)

        # Write to Bronze layer
        bronze_file = bronze_dir / f"{source_id}.html"
        metadata = write_bronze_if_changed(bronze_file, raw_content)

        # Add source metadata
        metadata.update(
            {
                "source_id": source_id,
                "title": source["title"],
                "url": url,
                "version": source.get("version", "current"),
                "jurisdiction": source.get("jurisdiction", "NO"),
                "effective_from": source.get("effective_from", ""),
                "effective_to": source.get("effective_to", ""),
                "domain": source.get("domain", ""),
                "source_type": source.get("source_type", ""),
                "publisher": source.get("publisher", ""),
                "crawl_freq": source.get("crawl_freq", ""),
            }
        )

        return metadata

    except Exception as e:
        log.error(f"Failed to ingest {source_id}: {e}")
        return {"source_id": source_id, "error": str(e), "success": False}


def main():
    """Main ingestion function."""
    # Setup paths
    project_root = Path(__file__).parent.parent
    sources_path = project_root / "configs" / "sources.csv"
    data_dir = project_root / "data"

    # Ensure directories exist
    directories = ensure_data_directories(data_dir)
    bronze_dir = directories["bronze"]

    # Load sources
    sources = load_sources(sources_path)
    log.info(f"Loaded {len(sources)} sources from {sources_path}")

    # Process each source
    results = []
    for source in sources:
        result = ingest_accounting_regulation(source, bronze_dir)
        results.append(result)

    # Save ingestion metadata
    metadata_file = bronze_dir / "ingestion_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Summary
    successful = sum(1 for r in results if r.get("success", True) and "error" not in r)
    changed = sum(1 for r in results if r.get("changed", False))

    log.info(
        f"Ingestion complete: {successful}/{len(sources)} successful, {changed} files changed"
    )

    return 0 if successful == len(sources) else 1


if __name__ == "__main__":
    sys.exit(main())
