#!/usr/bin/env python3
"""
Process Bronze layer data into Silver layer format.
Parses HTML content and extracts structured data with cleaned text.
Uses sources.csv as the source of truth for metadata classification.
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Any

from modules.base_script import BaseScript, register_script
from modules.parsers.lovdata_parser import parse_lovdata_html
from modules.data_io import ensure_data_directories, log
from modules.cleaners.legal_text_cleaner import (
    clean_legal_text,
    normalize_text,
    compute_stable_hash,
    extract_legal_metadata,
)


def load_sources_metadata(sources_file: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load sources.csv and create a lookup table by source_id.
    Returns dict mapping source_id to full metadata.
    """
    sources_lookup: Dict[str, Dict[str, Any]] = {}

    if not sources_file.exists():
        log.error(f"Sources file not found: {sources_file}")
        return sources_lookup

    try:
        with open(sources_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                source_id = row.get("source_id", "").strip()
                if source_id:
                    # Convert empty strings to None for optional fields
                    sources_lookup[source_id] = {
                        "source_id": source_id,
                        "title": row.get("title", "").strip(),
                        "url": row.get("url", "").strip(),
                        "version": row.get("version", "").strip() or "current",
                        "jurisdiction": row.get("jurisdiction", "").strip() or "NO",
                        "effective_from": row.get("effective_from", "").strip(),
                        "effective_to": row.get("effective_to", "").strip() or None,
                        "domain": row.get("domain", "").strip(),
                        "source_type": row.get("source_type", "").strip(),
                        "publisher": row.get("publisher", "").strip(),
                        "crawl_freq": row.get("crawl_freq", "").strip(),
                    }

        log.info(f"Loaded {len(sources_lookup)} sources from {sources_file}")
        return sources_lookup

    except Exception as e:
        log.error(f"Error loading sources file {sources_file}: {e}")
        return sources_lookup


def get_source_metadata(
    law_id: str, sources_lookup: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Get source metadata for a given law_id from sources lookup table.
    Raises ValueError if law_id not found (no fallback to unknown).
    """
    if law_id not in sources_lookup:
        raise ValueError(
            f"Source '{law_id}' not found in sources.csv. Available sources: {list(sources_lookup.keys())}"
        )

    return sources_lookup[law_id]


def _build_section_url(section, source_metadata: Dict[str, Any]) -> str:
    """Build section-specific URL with anchor."""
    base_url = str(section.source_url or source_metadata.get("url", ""))
    if not base_url:
        return ""

    # Extract section label for anchor (e.g., "§ 3-1" -> "#§-3-1")
    section_label = ""
    if section.heading:
        section_match = re.match(r"(§\s*[\d\-]+)", str(section.heading))
        if section_match:
            section_label = section_match.group(1).strip()

    if section_label:
        # Convert "§ 3-1" to "#%C2%A73-1" for anchor (URL-encoded §)
        anchor = section_label.replace(" ", "").replace("§", "#%C2%A7")
        return f"{base_url}{anchor}"

    return base_url


def enhance_section_metadata_cleaned(
    section, source_metadata: Dict[str, Any], html_content: str, ingested_at: str
) -> Dict[str, Any]:
    """
    Enhance section with comprehensive metadata from sources.csv.
    Uses source_metadata as the authoritative source for classification.
    """
    # Clean the text content
    cleaned_text = clean_legal_text(section.text_plain)
    normalized_text = normalize_text(cleaned_text)

    # Compute stable hash
    stable_hash = compute_stable_hash(normalized_text)

    # Extract legal metadata
    legal_metadata = extract_legal_metadata(
        html_content,
        source_metadata,
        section.heading or "",
        section.path or "",
        normalized_text,
    )

    # Get current timestamps
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    processed_at = now.isoformat()

    # Count tokens consistently using normalized text
    token_count = len(normalized_text.split()) if normalized_text else 0

    # Extract section label from heading (e.g., "§ 1-1" from "§ 1-1. Saklig virkeområde")
    section_label = ""
    if section.heading:
        section_match = re.match(r"(§\s*[\d\-]+)", section.heading)
        if section_match:
            section_label = section_match.group(1).strip()

    # Build enhanced metadata using source_metadata as authoritative source
    enhanced = {
        # Original section fields
        "law_id": section.law_id,
        "section_id": section.section_id,
        "section_label": section_label,
        "path": section.path,
        "heading": section.heading,
        "text_plain": normalized_text,
        "source_url": _build_section_url(section, source_metadata),
        "sha256": stable_hash,
        # Domain and categorization (from sources.csv)
        "domain": source_metadata.get("domain", ""),
        "source_type": source_metadata.get("source_type", ""),
        "publisher": source_metadata.get("publisher", ""),
        # Versioning and effectiveness (from sources.csv)
        "version": source_metadata.get("version", "current"),
        "jurisdiction": source_metadata.get("jurisdiction", "NO"),
        "effective_from": source_metadata.get("effective_from", ""),
        "effective_to": legal_metadata.get("repeal_date", "")
        if legal_metadata.get("repealed", False)
        else source_metadata.get("effective_to", ""),
        # Legal metadata (improved parsing)
        "law_title": legal_metadata.get("law_title", source_metadata.get("title", "")),
        "chapter": legal_metadata.get("chapter", ""),
        "chapter_no": legal_metadata.get("chapter_no", ""),
        "chapter_title": legal_metadata.get("chapter_title", ""),
        "repealed": legal_metadata.get("repealed", False),
        "repeal_date": legal_metadata.get("repeal_date", ""),
        "amendments": legal_metadata.get("amendments", []),
        # Status normalization
        "status": "repealed" if legal_metadata.get("repealed", False) else "active",
        # Lineage timestamps
        "ingested_at": ingested_at,
        "processed_at": processed_at,
        # Quality metrics
        "token_count": token_count,
        "crawl_freq": source_metadata.get("crawl_freq", ""),
    }

    return enhanced


def process_lovdata_files(
    bronze_dir: Path,
    silver_dir: Path,
    sources_lookup: Dict[str, Dict[str, Any]],
    test_mode: bool = False,
    specific_files: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """Process Lovdata HTML files into Silver format with cleaned text using sources.csv metadata."""
    sections = []
    min_text_length = 50  # Minimum characters for quality check
    quality_stats = {"validation_issues": 0}  # Initialize quality stats for validation

    # Load ingestion metadata for timestamps
    metadata_file = bronze_dir / "ingestion_metadata.json"
    ingestion_metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata_list = json.load(f)
            # Create lookup by source_id for ingested_at timestamps
            for m in metadata_list:
                ingestion_metadata[m.get("source_id", "")] = m.get("ingested_at", "")

    # Find all HTML files in Bronze layer
    html_files = list(bronze_dir.glob("*.html"))

    # Filter files based on test mode or specific files
    if specific_files:
        html_files = [f for f in html_files if f.name in specific_files]
        log.info(f"Processing specific files: {[f.name for f in html_files]}")
    elif test_mode:
        # In test mode, process only 2-3 files for faster testing
        test_files = [
            "mva_law_2009.html",
            "regnskapsloven_1998.html",
            "bokforingsloven_2004.html",
        ]
        html_files = [f for f in html_files if f.name in test_files]
        log.info(
            f"Test mode: processing only {len(html_files)} files for faster testing"
        )

    log.info(f"Found {len(html_files)} HTML files to process")

    for html_file in html_files:
        if html_file.name == "ingestion_metadata.json":
            continue

        log.info(f"Processing {html_file.name}")

        try:
            # Read HTML content
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Quality check: ensure we have content
            if len(html_content.strip()) < min_text_length:
                log.warning(
                    f"Skipping {html_file.name}: content too short ({len(html_content)} chars)"
                )
                continue

            # Extract law_id from filename
            law_id = html_file.stem

            # Get source metadata from sources.csv (this will raise ValueError if not found)
            try:
                source_metadata = get_source_metadata(law_id, sources_lookup)
                log.info(
                    f"Found metadata for {law_id}: {source_metadata['domain']} domain, {source_metadata['source_type']} type"
                )
            except ValueError as e:
                log.error(f"Failed to find metadata for {law_id}: {e}")
                continue

            # Get ingested_at timestamp
            ingested_at = ingestion_metadata.get(law_id, "")
            if not ingested_at:
                from datetime import datetime, timezone

                ingested_at = datetime.now(timezone.utc).isoformat()
                log.warning(
                    f"No ingested_at timestamp for {law_id}, using current time"
                )

            # Parse HTML content
            parsed_sections = parse_lovdata_html(
                html=html_content,
                law_id=law_id,
                source_url=source_metadata.get("url", ""),
                sha256="",  # Will be computed in enhance_section_metadata_cleaned
            )

            # Enhance each section with comprehensive metadata from sources.csv
            for section in parsed_sections:
                enhanced = enhance_section_metadata_cleaned(
                    section, source_metadata, html_content, ingested_at
                )

                # For sections without source_url, try to use the section's source_url if available
                if not enhanced["source_url"] and section.source_url:
                    enhanced["source_url"] = section.source_url

                # Validate section quality
                validation_issues = validate_section_quality(enhanced)
                if validation_issues:
                    log.warning(
                        f"Section {section.section_id} has quality issues: {', '.join(validation_issues)}"
                    )
                    quality_stats["validation_issues"] = quality_stats.get(
                        "validation_issues", 0
                    ) + len(validation_issues)

                # Only reject if text is too short
                if len(enhanced["text_plain"]) < min_text_length:
                    log.warning(
                        f"Skipping section {section.section_id}: text too short ({len(enhanced['text_plain'])} chars)"
                    )
                    continue

                sections.append(enhanced)

            log.info(f"Extracted {len(parsed_sections)} sections from {html_file.name}")

        except Exception as e:
            log.error(f"Error processing {html_file.name}: {e}")
            continue

    return sections


def validate_section_quality(section: Dict[str, Any]) -> List[str]:
    """Validate section quality and return list of issues."""
    issues = []

    # Required fields that must be present and non-empty
    required_fields = [
        "law_id",
        "section_id",
        "section_label",
        "heading",
        "text_plain",
        "source_url",
        "domain",
        "source_type",
        "publisher",
        "version",
        "jurisdiction",
        "status",
        "sha256",
        "ingested_at",
        "processed_at",
    ]

    for field in required_fields:
        if field not in section or not section[field] or section[field] == "":
            issues.append(f"Missing or empty required field: {field}")

    # Validate specific field values
    if section.get("domain") not in ["tax", "accounting", "reporting", "compliance"]:
        issues.append(f"Invalid domain: {section.get('domain')}")

    if section.get("status") not in ["active", "repealed", "superseded"]:
        issues.append(f"Invalid status: {section.get('status')}")

    if section.get("source_type") not in ["law", "regulation", "guidance"]:
        issues.append(f"Invalid source_type: {section.get('source_type')}")

    # Validate text quality
    if len(section.get("text_plain", "")) < 50:
        issues.append(f"Text too short: {len(section.get('text_plain', ''))} chars")

    # Validate URL format
    source_url = section.get("source_url", "")
    if source_url and not (
        source_url.startswith("http://") or source_url.startswith("https://")
    ):
        issues.append(f"Invalid URL format: {source_url}")

    return issues


def save_silver_sections(sections: List[Dict[str, Any]], silver_dir: Path) -> None:
    """Save sections to Silver layer with quality reporting and domain grouping."""
    quality_stats: Dict[str, Any] = {
        "total_processed": len(sections),
        "total_saved": 0,
        "rejected_short_text": 0,
        "validation_issues": 0,
        "total_tokens": 0,
        "domains": {},
        "source_types": {},
        "publishers": {},
    }

    # Group sections by domain and collect statistics
    domain_sections: Dict[str, List[Dict[str, Any]]] = {}
    for section in sections:
        domain = section.get("domain", "")
        source_type = section.get("source_type", "")
        publisher = section.get("publisher", "")

        # Initialize domain tracking
        if domain not in domain_sections:
            domain_sections[domain] = []
            quality_stats["domains"][domain] = {"processed": 0, "saved": 0, "tokens": 0}

        # Initialize source type tracking
        if source_type not in quality_stats["source_types"]:
            quality_stats["source_types"][source_type] = 0

        # Initialize publisher tracking
        if publisher not in quality_stats["publishers"]:
            quality_stats["publishers"][publisher] = 0

        quality_stats["domains"][domain]["processed"] += 1

        # Basic quality check - only reject if text is too short
        if len(section.get("text_plain", "")) < 50:
            quality_stats["rejected_short_text"] += 1
            log.warning(
                f"Rejecting section {section.get('section_id', 'unknown')}: text too short"
            )
            continue

        # Add to collections
        domain_sections[domain].append(section)
        quality_stats["total_saved"] += 1
        quality_stats["domains"][domain]["saved"] += 1
        quality_stats["total_tokens"] += section.get("token_count", 0)
        quality_stats["domains"][domain]["tokens"] += section.get("token_count", 0)
        quality_stats["source_types"][source_type] += 1
        quality_stats["publishers"][publisher] += 1

    # Save combined sections
    all_sections = []
    for domain_sections_list in domain_sections.values():
        all_sections.extend(domain_sections_list)

    output_file = silver_dir / "law_sections.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_sections, f, indent=2, ensure_ascii=False)

    log.info(f"Saved {len(all_sections)} sections to {output_file}")

    # Also save by domain for easier access
    for domain, domain_sections_list in domain_sections.items():
        if domain_sections_list:
            domain_file = silver_dir / f"{domain}_sections.json"
            with open(domain_file, "w", encoding="utf-8") as f:
                json.dump(domain_sections_list, f, indent=2, ensure_ascii=False)

            log.info(
                f"Saved {len(domain_sections_list)} sections for domain '{domain}' to {domain_file}"
            )

    # Save quality report
    quality_file = silver_dir / "quality_report.json"
    with open(quality_file, "w", encoding="utf-8") as f:
        json.dump(quality_stats, f, indent=2, ensure_ascii=False)

    log.info(f"Quality report saved to {quality_file}")
    log.info(
        f"Quality stats: {quality_stats['total_saved']}/{quality_stats['total_processed']} sections saved"
    )
    log.info(f"Total tokens: {quality_stats['total_tokens']:,}")
    log.info(f"Rejected - short text: {quality_stats['rejected_short_text']}")
    log.info(f"Validation issues: {quality_stats['validation_issues']}")

    # Log domain breakdown
    for domain, stats in quality_stats["domains"].items():
        if stats["saved"] > 0:
            log.info(
                f"Domain '{domain}': {stats['saved']} sections, {stats['tokens']:,} tokens"
            )

    # Log source type breakdown
    for source_type, count in quality_stats["source_types"].items():
        if count > 0:
            log.info(f"Source type '{source_type}': {count} sections")

    # Log publisher breakdown
    for publisher, count in quality_stats["publishers"].items():
        if count > 0:
            log.info(f"Publisher '{publisher}': {count} sections")


@register_script("process-bronze-to-silver")
class ProcessBronzeToSilverScript(BaseScript):
    """Script to process Bronze layer data to Silver layer."""

    def __init__(self):
        super().__init__("process_bronze_to_silver")

    def _parse_args(self):
        """Parse command line arguments."""
        import argparse

        parser = argparse.ArgumentParser(description="Process Bronze to Silver data")
        parser.add_argument(
            "--test",
            action="store_true",
            help="Run in test mode (process only 2-3 files)",
        )
        parser.add_argument("--files", nargs="+", help="Process specific files only")
        return parser.parse_args()

    def _execute(self) -> int:
        """Execute the Bronze to Silver processing."""
        # Parse command line arguments
        args = self._parse_args()

        # Setup paths
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "data"
        sources_file = project_root / "configs" / "sources.csv"

        # Ensure directories exist
        directories = ensure_data_directories(data_dir)
        bronze_dir = directories["bronze"]
        silver_dir = directories["silver"]

        # Load sources metadata from sources.csv
        log.info("Loading sources metadata from sources.csv")
        sources_lookup = load_sources_metadata(sources_file)

        if not sources_lookup:
            log.error("Failed to load sources metadata. Cannot proceed.")
            return 1

        # Process Lovdata files with sources metadata
        sections = process_lovdata_files(
            bronze_dir,
            silver_dir,
            sources_lookup,
            test_mode=args.test,
            specific_files=args.files,
        )

        if not sections:
            log.warning("No sections extracted from Bronze layer")
            return 1

        # Save to Silver layer
        save_silver_sections(sections, silver_dir)

        # Log summary by domain
        domain_counts: dict[str, int] = {}
        for section in sections:
            domain = section.get("domain", "")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        log.info(f"Successfully processed {len(sections)} sections to Silver layer")
        for domain, count in domain_counts.items():
            log.info(f"Domain '{domain}': {count} sections")

        return 0


def main():
    """Main entry point."""
    script = ProcessBronzeToSilverScript()
    return script.main()


if __name__ == "__main__":
    main()
