#!/usr/bin/env python3
"""
Process Bronze layer data into Silver layer format.
Parses HTML content and extracts structured data with cleaned text.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add modules to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.parsers.lovdata_parser import parse_lovdata_html, Section
from modules.utils import ensure_data_directories, log
from modules.cleaners.improved_text_processing import (
    clean_legal_text, normalize_text, compute_stable_hash,
    extract_legal_metadata
)


def enhance_section_metadata_cleaned(
    section, metadata: Dict[str, Any], html_content: str
) -> Dict[str, Any]:
    """
    Enhance section with comprehensive metadata using improved parsing.
    More lenient about source URLs but strict about text cleaning.
    """
    # Clean the text content
    cleaned_text = clean_legal_text(section.text_plain)
    normalized_text = normalize_text(cleaned_text)
    
    # Compute stable hash
    stable_hash = compute_stable_hash(normalized_text)
    
    # Extract legal metadata
    legal_metadata = extract_legal_metadata(html_content, metadata)
    
    # Get current timestamps
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    processed_at = now.isoformat()
    ingested_at = metadata.get("ingested_at", now.isoformat())
    
    # Count tokens (rough approximation)
    token_count = len(normalized_text.split()) if normalized_text else 0
    
    # Build enhanced metadata
    enhanced = {
        # Original section fields
        "law_id": section.law_id,
        "section_id": section.section_id,
        "path": section.path,
        "heading": section.heading,
        "text_plain": normalized_text,
        "source_url": section.source_url or metadata.get("url", ""),
        "sha256": stable_hash,
        
        # Domain and categorization
        "domain": metadata.get("domain", "unknown"),
        "source_type": metadata.get("source_type", "unknown"),
        "publisher": metadata.get("publisher", "unknown"),
        
        # Versioning and effectiveness
        "version": metadata.get("version", "current"),
        "jurisdiction": metadata.get("jurisdiction", "NO"),
        "effective_from": metadata.get("effective_from", ""),
        "effective_to": metadata.get("effective_to", ""),
        
        # Legal metadata
        "law_title": legal_metadata.get("law_title", metadata.get("title", "")),
        "chapter": legal_metadata.get("chapter", ""),  # Clean chapter, not concatenated
        "repealed": legal_metadata.get("repealed", False),
        "amended_dates": legal_metadata.get("amended_dates", []),
        
        # Lineage timestamps
        "ingested_at": ingested_at,
        "processed_at": processed_at,
        
        # Quality metrics
        "token_count": token_count,
        "crawl_freq": metadata.get("crawl_freq", "unknown"),
    }
    
    return enhanced


def process_lovdata_files(bronze_dir: Path, silver_dir: Path) -> List[Dict[str, Any]]:
    """Process Lovdata HTML files into Silver format with cleaned text."""
    sections = []
    min_text_length = 50  # Minimum characters for quality check

    # Load metadata
    metadata_file = bronze_dir / "ingestion_metadata.json"
    if not metadata_file.exists():
        log.error("No ingestion metadata found")
        return sections

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata_list = json.load(f)

    log.info(f"Found {len(metadata_list)} sources to process")

    # Find all HTML files in Bronze layer
    html_files = list(bronze_dir.glob("*.html"))
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
                log.warning(f"Skipping {html_file.name}: content too short ({len(html_content)} chars)")
                continue

            # Extract law_id from filename
            law_id = html_file.stem

            # Find metadata for this file
            file_metadata: Dict[str, Any] = next(
                (m for m in metadata_list if m.get("source_id") == law_id), {}
            )

            # If no metadata found, create basic metadata
            if not file_metadata:
                log.warning(f"No metadata found for {law_id}, creating basic metadata")
                file_metadata = {
                    "source_id": law_id,
                    "url": "",  # Will be filled from section if available
                    "sha256": "",
                    "domain": "unknown",
                    "source_type": "law",  # Default assumption
                    "publisher": "unknown",
                    "title": law_id.replace("_", " ").title(),
                    "version": "current",
                    "jurisdiction": "NO",
                    "effective_from": "",
                    "effective_to": "",
                    "crawl_freq": "unknown"
                }

            # Parse HTML content
            parsed_sections = parse_lovdata_html(
                html=html_content,
                law_id=law_id,
                source_url=file_metadata.get("url", ""),
                sha256=file_metadata.get("sha256", ""),
            )

            # Enhance each section with comprehensive metadata
            for section in parsed_sections:
                enhanced = enhance_section_metadata_cleaned(section, file_metadata, html_content)

                # For sections without source_url, try to use the section's source_url if available
                if not enhanced["source_url"] and section.source_url:
                    enhanced["source_url"] = section.source_url

                # Only reject if text is too short - be more lenient about source URLs
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


def save_silver_sections(sections: List[Dict[str, Any]], silver_dir: Path) -> None:
    """Save sections to Silver layer with quality reporting and domain grouping."""
    quality_stats = {
        'total_processed': len(sections),
        'total_saved': 0,
        'rejected_short_text': 0,
        'total_tokens': 0,
        'domains': {}
    }

    # Group sections by domain
    domain_sections = {}
    for section in sections:
        domain = section.get('domain', 'unknown')
        if domain not in domain_sections:
            domain_sections[domain] = []
            quality_stats['domains'][domain] = {'processed': 0, 'saved': 0, 'tokens': 0}

        quality_stats['domains'][domain]['processed'] += 1

        # Basic quality check - only reject if text is too short
        if len(section.get("text_plain", "")) < 50:
            quality_stats['rejected_short_text'] += 1
            log.warning(f"Rejecting section {section.get('section_id', 'unknown')}: text too short")
            continue

        # Add to collections
        domain_sections[domain].append(section)
        quality_stats['total_saved'] += 1
        quality_stats['domains'][domain]['saved'] += 1
        quality_stats['total_tokens'] += section.get('token_count', 0)
        quality_stats['domains'][domain]['tokens'] += section.get('token_count', 0)

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

            log.info(f"Saved {len(domain_sections_list)} sections for domain '{domain}' to {domain_file}")

    # Save quality report
    quality_file = silver_dir / "quality_report.json"
    with open(quality_file, "w", encoding="utf-8") as f:
        json.dump(quality_stats, f, indent=2, ensure_ascii=False)

    log.info(f"Quality report saved to {quality_file}")
    log.info(f"Quality stats: {quality_stats['total_saved']}/{quality_stats['total_processed']} sections saved")
    log.info(f"Total tokens: {quality_stats['total_tokens']:,}")
    log.info(f"Rejected - short text: {quality_stats['rejected_short_text']}")


def main():
    """Main processing function."""
    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    # Ensure directories exist
    directories = ensure_data_directories(data_dir)
    bronze_dir = directories["bronze"]
    silver_dir = directories["silver"]

    # Process Lovdata files
    sections = process_lovdata_files(bronze_dir, silver_dir)

    if not sections:
        log.warning("No sections extracted from Bronze layer")
        return 1

    # Save to Silver layer
    save_silver_sections(sections, silver_dir)

    # Log summary by domain
    domain_counts = {}
    for section in sections:
        domain = section.get('domain', 'unknown')
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    log.info(f"Successfully processed {len(sections)} sections to Silver layer")
    for domain, count in domain_counts.items():
        log.info(f"Domain '{domain}': {count} sections")

    return 0


if __name__ == "__main__":
    sys.exit(main())