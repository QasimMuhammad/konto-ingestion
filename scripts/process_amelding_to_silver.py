#!/usr/bin/env python3
"""
Process A-meldingen Bronze data to Silver layer.
Extracts A-melding rules and guidance from Skatteetaten and Altinn content.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from modules.base_script import BaseScript, register_script
from modules.parsers.amelding_parser import (
    parse_amelding_overview,
    parse_amelding_forms,
)
from modules.data_io import ensure_data_directories, log, compute_stable_hash


def process_amelding_sources(
    sources: List[Dict[str, str]], bronze_dir: Path, silver_dir: Path
) -> Dict[str, Any]:
    """Process A-meldingen sources from Bronze to Silver."""
    all_rules: list[Any] = []
    processing_stats: dict[str, Any] = {
        "total_sources": 0,
        "processed_sources": 0,
        "total_rules": 0,
        "errors": [],
    }

    for source in sources:
        source_id = source["source_id"]
        url = source["url"]
        source_type = source.get("source_type", "guidance")

        processing_stats["total_sources"] += 1

        log.info(f"Processing A-meldingen source: {source_id}")

        try:
            # Read Bronze HTML file
            bronze_file = bronze_dir / f"{source_id}.html"
            if not bronze_file.exists():
                log.warning(f"Bronze file not found: {bronze_file}")
                continue

            html_content = bronze_file.read_text(encoding="utf-8")
            sha256 = compute_stable_hash(html_content)

            # Parse A-meldingen content
            if "overview" in url.lower():
                rules = parse_amelding_overview(html_content, url, sha256)
            elif "form" in url.lower():
                rules = parse_amelding_forms(html_content, url, sha256)
            else:
                # Try both parsers
                rules = parse_amelding_overview(html_content, url, sha256)
                rules.extend(parse_amelding_forms(html_content, url, sha256))

            # Add metadata to rules
            for rule in rules:
                rule_dict = {
                    "rule_id": rule.rule_id,
                    "title": rule.title,
                    "description": rule.description,
                    "category": rule.category,
                    "applies_to": rule.applies_to,
                    "requirements": rule.requirements,
                    "examples": rule.examples,
                    "source_url": rule.source_url,
                    "sha256": rule.sha256,
                    "domain": "reporting",
                    "source_type": source_type,
                    "publisher": source.get("publisher", "Skatteetaten"),
                    "jurisdiction": "NO",
                    "is_current": True,
                    "effective_from": source.get("effective_from"),
                    "effective_to": source.get("effective_to"),
                    "priority": determine_priority(rule.category),
                    "complexity": determine_complexity(rule.description),
                    "last_updated": datetime.now().isoformat(),
                }
                all_rules.append(rule_dict)

            processing_stats["processed_sources"] += 1
            processing_stats["total_rules"] += len(rules)

            log.info(f"Extracted {len(rules)} A-meldingen rules from {source_id}")

        except Exception as e:
            error_msg = f"Error processing {source_id}: {str(e)}"
            log.error(error_msg)
            processing_stats["errors"].append(error_msg)

    # Write to Silver layer
    silver_file = silver_dir / "amelding_rules.json"
    with open(silver_file, "w", encoding="utf-8") as f:
        json.dump(all_rules, f, indent=2, ensure_ascii=False)

    log.info(f"Wrote {len(all_rules)} A-meldingen rules to {silver_file}")

    return processing_stats


def determine_priority(category: str) -> str:
    """Determine priority level for the rule."""
    high_priority = ["submission_deadlines", "employer_obligations"]
    medium_priority = ["salary_reporting", "tax_deductions"]

    if category in high_priority:
        return "high"
    elif category in medium_priority:
        return "medium"
    else:
        return "low"


def determine_complexity(description: str) -> str:
    """Determine complexity level based on description length and content."""
    word_count = len(description.split())

    if word_count > 200 or any(
        word in description.lower()
        for word in ["kompleks", "complex", "avansert", "advanced"]
    ):
        return "high"
    elif word_count > 100 or any(
        word in description.lower() for word in ["moderat", "moderate", "middels"]
    ):
        return "medium"
    else:
        return "low"


@register_script("process-amelding-to-silver")
class ProcessAmeldingToSilverScript(BaseScript):
    """Script to process A-meldingen from Bronze to Silver layer."""

    def __init__(self):
        super().__init__("process_amelding_to_silver")

    def _execute(self) -> int:
        """Execute the A-meldingen processing."""
        # Setup paths
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        bronze_dir = project_root / "data" / "bronze"
        silver_dir = project_root / "data" / "silver"
        sources_file = project_root / "configs" / "sources.csv"

        # Ensure directories exist
        ensure_data_directories()

        # Load A-meldingen sources
        import csv

        amelding_sources = []

        with open(sources_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (
                    row.get("domain") == "reporting"
                    and "amelding" in row.get("source_id", "").lower()
                ):
                    amelding_sources.append(row)

        if not amelding_sources:
            log.error("No A-meldingen sources found in sources.csv")
            return 1

        log.info(f"Found {len(amelding_sources)} A-meldingen sources")

        # Process sources
        stats = process_amelding_sources(amelding_sources, bronze_dir, silver_dir)

        # Print summary
        log.info("\n" + "=" * 50)
        log.info("A-MELDINGEN PROCESSING SUMMARY")
        log.info("=" * 50)
        log.info(f"Total sources: {stats['total_sources']}")
        log.info(f"Processed sources: {stats['processed_sources']}")
        log.info(f"Total rules extracted: {stats['total_rules']}")
        log.info(f"Errors: {len(stats['errors'])}")

        if stats["errors"]:
            log.error("\nErrors:")
            for error in stats["errors"]:
                log.error(f"  • {error}")

        log.info("=" * 50)
        return 0


def main():
    """Main entry point."""
    script = ProcessAmeldingToSilverScript()
    return script.main()


if __name__ == "__main__":
    main()
