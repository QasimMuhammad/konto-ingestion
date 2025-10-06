#!/usr/bin/env python3
"""
Process VAT rates Bronze data to Silver layer.
Extracts VAT rates from Skatteetaten HTML content.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add modules to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.parsers.rates_parser import parse_mva_rates, get_standard_rates
from modules.data_io import ensure_data_directories, log, compute_stable_hash


def process_rates_sources(
    sources: List[Dict[str, str]], bronze_dir: Path, silver_dir: Path
) -> Dict[str, Any]:
    """Process VAT rates sources from Bronze to Silver."""
    all_rates = []
    processing_stats = {
        "total_sources": 0,
        "processed_sources": 0,
        "total_rates": 0,
        "errors": [],
    }

    for source in sources:
        source_id = source["source_id"]
        url = source["url"]

        processing_stats["total_sources"] += 1

        log.info(f"Processing rates source: {source_id}")

        try:
            # Read Bronze HTML file
            bronze_file = bronze_dir / f"{source_id}.html"
            if not bronze_file.exists():
                log.warning(f"Bronze file not found: {bronze_file}")
                continue

            html_content = bronze_file.read_text(encoding="utf-8")
            sha256 = compute_stable_hash(html_content)

            # Parse rates content
            rates = parse_mva_rates(html_content, url, sha256)

            # If no rates found, use standard rates as fallback
            if not rates:
                log.warning(f"No rates found in {source_id}, using standard rates")
                rates = get_standard_rates()
                # Update source info for standard rates
                for rate in rates:
                    rate.source_url = url
                    rate.sha256 = sha256

            # Add metadata to rates
            for rate in rates:
                rate_dict = {
                    "kind": rate.kind,
                    "value": rate.value,
                    "percentage": rate.percentage,
                    "valid_from": rate.valid_from,
                    "valid_to": rate.valid_to,
                    "description": rate.description,
                    "source_url": rate.source_url,
                    "sha256": rate.sha256,
                    "domain": "tax",
                    "source_type": "rates",
                    "publisher": source.get("publisher", "Skatteetaten"),
                    "jurisdiction": "NO",
                    "is_current": rate.valid_to is None
                    or rate.valid_to >= datetime.now().strftime("%Y-%m-%d"),
                    "category": rate.category,
                    "applies_to": rate.applies_to if hasattr(rate, 'applies_to') else get_applies_to(rate.kind),
                    "exceptions": rate.exceptions if hasattr(rate, 'exceptions') else [],
                    "notes": rate.notes if hasattr(rate, 'notes') else None,
                    "last_updated": rate.last_updated if hasattr(rate, 'last_updated') else datetime.now().isoformat(),
                }
                all_rates.append(rate_dict)

            processing_stats["processed_sources"] += 1
            processing_stats["total_rates"] += len(rates)

            log.info(f"Extracted {len(rates)} rates from {source_id}")

        except Exception as e:
            error_msg = f"Error processing {source_id}: {str(e)}"
            log.error(error_msg)
            processing_stats["errors"].append(error_msg)

    # Write to Silver layer
    silver_file = silver_dir / "rate_table.json"
    with open(silver_file, "w", encoding="utf-8") as f:
        json.dump(all_rates, f, indent=2, ensure_ascii=False)

    log.info(f"Wrote {len(all_rates)} VAT rates to {silver_file}")

    return processing_stats


def get_applies_to(kind: str) -> List[str]:
    """Get what a rate kind applies to."""
    applies_to_map = {
        "standard": ["Most goods and services", "General sales", "Most transactions"],
        "lav": ["Food items", "Transportation", "Hotels", "Books", "Newspapers"],
        "null": ["Exports", "Some services", "Certain goods", "Zero-rated items"],
        "høy": ["Luxury goods", "Tobacco", "Alcohol", "High-value items"],
        "mva": ["All VAT-applicable transactions"],
    }

    return applies_to_map.get(kind, ["General"])


def main():
    """Main processing function."""
    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    bronze_dir = project_root / "data" / "bronze"
    silver_dir = project_root / "data" / "silver"
    sources_file = project_root / "configs" / "sources.csv"

    # Ensure directories exist
    ensure_data_directories()

    # Load rates sources
    import csv

    rates_sources = []

    with open(sources_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (
                row.get("source_type") == "rates"
                or "rates" in row.get("source_id", "").lower()
            ):
                rates_sources.append(row)

    if not rates_sources:
        log.error("No rates sources found in sources.csv")
        sys.exit(1)

    log.info(f"Found {len(rates_sources)} rates sources")

    # Process sources
    stats = process_rates_sources(rates_sources, bronze_dir, silver_dir)

    # Print summary
    print("\n" + "=" * 50)
    print("VAT RATES PROCESSING SUMMARY")
    print("=" * 50)
    print(f"Total sources: {stats['total_sources']}")
    print(f"Processed sources: {stats['processed_sources']}")
    print(f"Total rates extracted: {stats['total_rates']}")
    print(f"Errors: {len(stats['errors'])}")

    if stats["errors"]:
        print("\nErrors:")
        for error in stats["errors"]:
            print(f"  • {error}")

    print("=" * 50)


if __name__ == "__main__":
    main()
