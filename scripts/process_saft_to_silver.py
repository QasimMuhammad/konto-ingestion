#!/usr/bin/env python3
"""
Process SAF-T Bronze data to Silver layer.
Extracts specification nodes from SAF-T documentation.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from modules.base_script import BaseScript, register_script
from modules.parsers.saft_parser import parse_saft_page, parse_saft_documentation
from modules.data_io import ensure_data_directories, log, compute_stable_hash


def process_saft_sources(
    sources: List[Dict[str, str]], bronze_dir: Path, silver_dir: Path
) -> Dict[str, Any]:
    """Process SAF-T sources from Bronze to Silver."""
    all_nodes = []
    processing_stats = {
        "total_sources": 0,
        "processed_sources": 0,
        "total_nodes": 0,
        "errors": [],
    }

    for source in sources:
        source_id = source["source_id"]
        url = source["url"]
        version = source.get("version", "1.30")

        processing_stats["total_sources"] += 1

        log.info(f"Processing SAF-T source: {source_id}")

        try:
            # Read Bronze HTML file
            bronze_file = bronze_dir / f"{source_id}.html"
            if not bronze_file.exists():
                log.warning(f"Bronze file not found: {bronze_file}")
                continue

            html_content = bronze_file.read_text(encoding="utf-8")
            sha256 = compute_stable_hash(html_content)

            # Parse SAF-T content
            if "docs" in source_id.lower():
                # Documentation page - use documentation parser
                nodes = parse_saft_documentation(html_content, version, url, sha256)
            else:
                # Main specification page - use main parser
                nodes = parse_saft_page(html_content, version, url, sha256)

            # Add metadata to nodes
            for node in nodes:
                node_dict = {
                    "spec": node.spec,
                    "version": node.version,
                    "node_path": node.node_path,
                    "cardinality": node.cardinality,
                    "description": node.description,
                    "source_url": node.source_url,
                    "sha256": node.sha256,
                    "domain": "reporting",
                    "source_type": "spec",
                    "publisher": source.get("publisher", "Skatteetaten"),
                    "is_required": node.cardinality in ["1..1", "1..*"],
                    "data_type": None,
                    "max_length": None,
                    "pattern": None,
                    "parent_path": get_parent_path(node.node_path),
                    "level": get_node_level(node.node_path),
                    "is_leaf": is_leaf_node(node.node_path),
                    "examples": [],
                    "notes": None,
                    "last_updated": datetime.now().isoformat(),
                }
                all_nodes.append(node_dict)

            processing_stats["processed_sources"] += 1
            processing_stats["total_nodes"] += len(nodes)

            log.info(f"Extracted {len(nodes)} nodes from {source_id}")

        except Exception as e:
            error_msg = f"Error processing {source_id}: {str(e)}"
            log.error(error_msg)
            processing_stats["errors"].append(error_msg)

    # Write to Silver layer
    silver_file = silver_dir / "saft_v1_3_nodes.json"
    with open(silver_file, "w", encoding="utf-8") as f:
        json.dump(all_nodes, f, indent=2, ensure_ascii=False)

    log.info(f"Wrote {len(all_nodes)} SAF-T nodes to {silver_file}")

    return processing_stats


def get_parent_path(node_path: str) -> str:
    """Extract parent path from node path."""
    if not node_path:
        return ""

    parts = node_path.split(".")
    if len(parts) > 1:
        return ".".join(parts[:-1])
    return ""


def get_node_level(node_path: str) -> int:
    """Calculate hierarchy level from node path."""
    if not node_path:
        return 0

    return node_path.count(".") + 1


def is_leaf_node(node_path: str) -> bool:
    """Determine if node is a leaf node (no children expected)."""
    if not node_path:
        return True

    # Simple heuristic: if path contains common leaf indicators
    leaf_indicators = ["value", "text", "amount", "date", "id", "code", "number"]
    return any(indicator in node_path.lower() for indicator in leaf_indicators)


@register_script("process-saft-to-silver")
class ProcessSaftToSilverScript(BaseScript):
    """Script to process SAF-T from Bronze to Silver layer."""

    def __init__(self):
        super().__init__("process_saft_to_silver")

    def _execute(self) -> int:
        """Execute the SAF-T processing."""
        # Setup paths
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        bronze_dir = project_root / "data" / "bronze"
        silver_dir = project_root / "data" / "silver"
        sources_file = project_root / "configs" / "sources.csv"

        # Ensure directories exist
        ensure_data_directories()

        # Load SAF-T sources
        import csv

        saft_sources = []

        with open(sources_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (
                    row.get("domain") == "reporting"
                    and "saft" in row.get("source_id", "").lower()
                ):
                    saft_sources.append(row)

        if not saft_sources:
            log.error("No SAF-T sources found in sources.csv")
            return 1

        log.info(f"Found {len(saft_sources)} SAF-T sources")

        # Process sources
        stats = process_saft_sources(saft_sources, bronze_dir, silver_dir)

        # Print summary
        print("\n" + "=" * 50)
        print("SAF-T PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Total sources: {stats['total_sources']}")
        print(f"Processed sources: {stats['processed_sources']}")
        print(f"Total nodes extracted: {stats['total_nodes']}")
        print(f"Errors: {len(stats['errors'])}")

        if stats["errors"]:
            print("\nErrors:")
            for error in stats["errors"]:
                print(f"  • {error}")

        print("=" * 50)
        return 0


def main():
    """Main entry point."""
    script = ProcessSaftToSilverScript()
    return script.main()


if __name__ == "__main__":
    main()
