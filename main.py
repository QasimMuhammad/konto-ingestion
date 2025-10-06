#!/usr/bin/env python3
"""
Main entry point for konto-ingestion.
Handles domain-based ingestion and crawl scheduling.
"""

import argparse
import sys
from typing import List, Dict, Any

from modules.logger import logger as log
from modules.settings import get_sources_file


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
    return parser.parse_args()


def load_all_sources() -> List[Dict[str, Any]]:
    """Load all sources from CSV file."""
    import csv

    sources = []
    sources_path = get_sources_file()

    with open(sources_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sources.append(row)
    return sources


def get_sources_by_domain(domain: str) -> List[Dict[str, Any]]:
    """Get sources filtered by domain."""
    all_sources = load_all_sources()
    return [s for s in all_sources if s.get("domain", "").lower() == domain.lower()]


def get_sources_by_crawl_freq(freq: str) -> List[Dict[str, Any]]:
    """Get sources filtered by crawl frequency."""
    all_sources = load_all_sources()
    return [s for s in all_sources if s.get("crawl_freq", "").lower() == freq.lower()]


def run_ingestion(domain: str | None = None, freq: str | None = None) -> int:
    """Run ingestion for specified domain or frequency."""
    if domain:
        log.info(f"Running ingestion for domain: {domain}")
        sources = get_sources_by_domain(domain)

        if domain == "tax":
            from scripts.ingest_tax_regs import main as ingest_tax

            return ingest_tax()
        elif domain == "accounting":
            from scripts.ingest_accounting_regs import main as ingest_accounting

            return ingest_accounting()
        elif domain == "reporting":
            from scripts.ingest_reporting_regs import main as ingest_reporting

            return ingest_reporting()
        else:
            log.error(f"Unknown domain: {domain}")
            return 1

    elif freq:
        log.info(f"Running ingestion for frequency: {freq}")
        sources = get_sources_by_crawl_freq(freq)

        # Group by domain and run appropriate scripts
        domains = {s.get("domain", "") for s in sources if s.get("domain")}
        results = []

        for dom in domains:
            if dom:
                result = run_ingestion(domain=dom)
                results.append(result)

        return 0 if all(r == 0 for r in results) else 1

    else:
        # Run all domains
        log.info("Running ingestion for all domains")
        domains = {"tax", "accounting", "reporting"}
        results = []

        for dom in domains:
            result = run_ingestion(domain=dom)
            results.append(result)

        return 0 if all(r == 0 for r in results) else 1


def list_sources(domain: str | None = None, freq: str | None = None) -> None:
    """List sources with optional filtering."""
    if domain:
        sources = get_sources_by_domain(domain)
        print(f"\nSources for domain '{domain}':")
    elif freq:
        sources = get_sources_by_crawl_freq(freq)
        print(f"\nSources with crawl frequency '{freq}':")
    else:
        sources = load_all_sources()
        print("\nAll sources:")

    if not sources:
        print("No sources found.")
        return

    for source in sources:
        print(f"  {source['source_id']}: {source['title']}")
        print(f"    Domain: {source.get('domain', 'N/A')}")
        print(f"    Type: {source.get('source_type', 'N/A')}")
        print(f"    Publisher: {source.get('publisher', 'N/A')}")
        print(f"    Frequency: {source.get('crawl_freq', 'N/A')}")
        print()


def main():
    """Main entry point."""
    args = parse_args()

    if args.command == "ingest":
        return run_ingestion(domain=args.domain, freq=args.freq)
    elif args.command == "list":
        list_sources(domain=args.domain, freq=args.freq)
        return 0
    else:
        log.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
