#!/usr/bin/env python3
"""
Main entry point for konto-ingestion pipeline.
Orchestrates data ingestion from sources to Bronze and Silver layers.
"""

import argparse
import csv
import sys
from typing import List, Dict, Any

from modules.data_io import ensure_data_directories, log
from modules.settings import (
    get_sources_file,
    get_data_dir,
    get_bronze_dir,
    get_silver_dir,
)
from modules.pipeline.ingestion_pipeline import IngestionPipeline, fetch_html_source
from modules.pipeline.domain_pipelines import (
    LegalTextProcessingPipeline,
    RatesProcessingPipeline,
    AmeldingProcessingPipeline,
    SaftProcessingPipeline,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Konto Ingestion Pipeline")
    parser.add_argument("command", choices=["ingest", "list"], help="Command to run")
    parser.add_argument(
        "--domain", choices=["tax", "accounting", "reporting"], help="Filter by domain"
    )
    parser.add_argument(
        "--freq",
        choices=["monthly", "quarterly", "onchange"],
        help="Filter by crawl frequency",
    )
    parser.add_argument(
        "--bronze-only",
        action="store_true",
        help="Only ingest to Bronze layer (skip Silver processing)",
    )
    return parser.parse_args()


def load_all_sources() -> List[Dict[str, Any]]:
    """Load all sources from CSV file."""
    sources_path = get_sources_file()
    with open(sources_path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_sources_by_domain(domain: str) -> List[Dict[str, Any]]:
    """Get sources filtered by domain."""
    all_sources = load_all_sources()
    return [s for s in all_sources if s.get("domain", "").lower() == domain.lower()]


def get_sources_by_crawl_freq(freq: str) -> List[Dict[str, Any]]:
    """Get sources filtered by crawl frequency."""
    all_sources = load_all_sources()
    return [s for s in all_sources if s.get("crawl_freq", "").lower() == freq.lower()]


def run_bronze_ingestion(domain: str | None = None) -> int:
    """Run Bronze layer ingestion: sources → bronze."""
    sources_file = get_sources_file()
    data_dir = get_data_dir()
    bronze_dir = get_bronze_dir()

    ensure_data_directories(data_dir)

    if domain:
        log.info(f"Ingesting Bronze layer for domain: {domain}")

        # Use simplified IngestionPipeline with domain parameter
        pipeline = IngestionPipeline(
            f"{domain}_ingestion", fetch_html_source, domain=domain
        )
        pipeline.setup(sources_file, bronze_dir)
        result = pipeline.execute()

        return 0 if result.failed_items == 0 else 1

    else:
        log.info("Ingesting Bronze layer for all domains")
        failed_counts: list[int] = []
        domains = ["tax", "accounting", "reporting"]

        for domain_name in domains:
            log.info(f"\n{'=' * 60}")
            log.info(f"Ingesting domain: {domain_name}")
            log.info(f"{'=' * 60}")

            pipeline = IngestionPipeline(
                f"{domain_name}_ingestion", fetch_html_source, domain=domain_name
            )
            pipeline.setup(sources_file, bronze_dir)
            result = pipeline.execute()
            failed_counts.append(result.failed_items)

        log.info(f"\n{'=' * 60}")
        log.info("BRONZE INGESTION COMPLETE")
        log.info(f"{'=' * 60}")

        return 0 if all(failed == 0 for failed in failed_counts) else 1


def run_silver_processing(domain: str | None = None) -> int:
    """Run Silver layer processing: bronze → silver."""
    sources_file = get_sources_file()
    data_dir = get_data_dir()
    bronze_dir = get_bronze_dir()
    silver_dir = get_silver_dir()

    ensure_data_directories(data_dir)

    # Map of processing pipelines
    pipeline_map = {
        "legal": LegalTextProcessingPipeline(),
        "rates": RatesProcessingPipeline(),
        "amelding": AmeldingProcessingPipeline(),
        "saft": SaftProcessingPipeline(),
    }

    if domain:
        # Filter pipelines based on domain
        domain_type_map = {
            "tax": ["legal", "rates"],
            "accounting": ["saft"],
            "reporting": ["amelding"],
        }

        types_to_process = domain_type_map.get(domain, [])
        if not types_to_process:
            log.error(f"No processing pipelines for domain: {domain}")
            return 1

        domain_failed_counts: list[int] = []
        for proc_type in types_to_process:
            if proc_type in pipeline_map:
                log.info(f"\n{'=' * 60}")
                log.info(f"Processing type: {proc_type}")
                log.info(f"{'=' * 60}")
                pipeline = pipeline_map[proc_type]
                pipeline.setup(sources_file, bronze_dir, silver_dir)
                result = pipeline.execute()
                domain_failed_counts.append(result.failed_items)

        return 0 if all(failed == 0 for failed in domain_failed_counts) else 1

    else:
        log.info("Processing all Bronze files to Silver")
        all_failed_counts: list[int] = []

        for proc_type, pipeline in pipeline_map.items():
            log.info(f"\n{'=' * 60}")
            log.info(f"Processing type: {proc_type}")
            log.info(f"{'=' * 60}")
            pipeline.setup(sources_file, bronze_dir, silver_dir)
            result = pipeline.execute()
            all_failed_counts.append(result.failed_items)

        log.info(f"\n{'=' * 60}")
        log.info("SILVER PROCESSING COMPLETE")
        log.info(f"{'=' * 60}")

        return 0 if all(failed == 0 for failed in all_failed_counts) else 1


def run_ingestion(
    domain: str | None = None, freq: str | None = None, bronze_only: bool = False
) -> int:
    """
    Run ingestion pipeline: sources → bronze → silver.

    Args:
        domain: Filter by domain (tax, accounting, reporting)
        freq: Filter by crawl frequency (not implemented yet)
        bronze_only: If True, only run bronze ingestion
    """
    log.info("=" * 80)
    log.info("KONTO INGESTION PIPELINE")
    log.info("=" * 80)

    # Stage 1: Bronze Ingestion
    log.info("\n" + "=" * 80)
    log.info("STAGE 1: INGESTING BRONZE FROM SOURCES")
    log.info("=" * 80)

    if run_bronze_ingestion(domain) != 0:
        log.error("Bronze ingestion failed.")
        return 1

    if bronze_only:
        log.info("\n" + "=" * 80)
        log.info("BRONZE-ONLY MODE: SKIPPING SILVER PROCESSING")
        log.info("=" * 80)
        return 0

    # Stage 2: Silver Processing
    log.info("\n" + "=" * 80)
    log.info("STAGE 2: PROCESSING BRONZE TO SILVER")
    log.info("=" * 80)

    if run_silver_processing(domain) != 0:
        return 1

    log.info("\n" + "=" * 80)
    log.info("PIPELINE COMPLETE")
    log.info("=" * 80)
    log.info("✓ All stages completed successfully")
    return 0


def list_sources(domain: str | None = None, freq: str | None = None) -> None:
    """List sources with optional filtering."""
    if domain:
        sources = get_sources_by_domain(domain)
        log.info(f"\nSources for domain '{domain}':")
    elif freq:
        sources = get_sources_by_crawl_freq(freq)
        log.info(f"\nSources with crawl frequency '{freq}':")
    else:
        sources = load_all_sources()
        log.info("\nAll sources:")

    if not sources:
        log.info("No sources found.")
        return

    for source in sources:
        log.info(f"  {source['source_id']}: {source['title']}")
        log.info(f"    Domain: {source.get('domain', 'N/A')}")
        log.info(f"    Type: {source.get('source_type', 'N/A')}")
        log.info(f"    Publisher: {source.get('publisher', 'N/A')}")
        log.info(f"    Frequency: {source.get('crawl_freq', 'N/A')}")
        log.info("")


def main():
    """Main entry point."""
    args = parse_args()

    if args.command == "ingest":
        return run_ingestion(
            domain=args.domain, freq=args.freq, bronze_only=args.bronze_only
        )
    elif args.command == "list":
        list_sources(domain=args.domain, freq=args.freq)
        return 0
    else:
        log.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
