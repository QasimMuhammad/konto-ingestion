#!/usr/bin/env python3
"""
Export Gold layer glossary training data from Silver layer.

Generates tax and accounting glossary JSONL files for LLM fine-tuning.
"""

import argparse
import json
import sys
from pathlib import Path

from modules.exporters.glossary_exporter import GlossaryExporter
from modules.logger import logger


def load_json(file_path: Path) -> list[dict]:
    """Load JSON data from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def export_tax_glossary(
    silver_dir: Path,
    output_dir: Path,
    split_ratio: float = 0.8,
) -> dict:
    """
    Export tax glossary from law sections.

    Args:
        silver_dir: Silver layer directory
        output_dir: Gold layer output directory
        split_ratio: Train/val split ratio

    Returns:
        Export statistics
    """
    logger.info("=" * 60)
    logger.info("EXPORTING TAX GLOSSARY")
    logger.info("=" * 60)

    law_sections_path = silver_dir / "law_sections.json"
    if not law_sections_path.exists():
        logger.error(f"Law sections file not found: {law_sections_path}")
        return {}

    law_sections = load_json(law_sections_path)
    logger.info(f"Loaded {len(law_sections)} law sections")

    tax_sections = [s for s in law_sections if s.get("domain") == "tax"]
    logger.info(f"Filtered to {len(tax_sections)} tax sections")

    exporter = GlossaryExporter(
        output_dir=output_dir,
        domain="tax",
        split_ratio=split_ratio,
    )

    stats = exporter.export(
        source_data=tax_sections,
        output_filename="tax_glossary.jsonl",
    )

    return stats


def export_accounting_glossary(
    silver_dir: Path,
    output_dir: Path,
    split_ratio: float = 0.8,
) -> dict:
    """
    Export accounting glossary from SAF-T nodes and Chart of Accounts.

    Args:
        silver_dir: Silver layer directory
        output_dir: Gold layer output directory
        split_ratio: Train/val split ratio

    Returns:
        Export statistics
    """
    logger.info("=" * 60)
    logger.info("EXPORTING ACCOUNTING GLOSSARY")
    logger.info("=" * 60)

    saft_path = silver_dir / "saft_v1_3_nodes.json"
    coa_path = silver_dir / "chart_of_accounts.json"

    accounting_data = []

    if saft_path.exists():
        saft_nodes = load_json(saft_path)
        logger.info(f"Loaded {len(saft_nodes)} SAF-T nodes")
        accounting_data.extend(saft_nodes)
    else:
        logger.warning(f"SAF-T nodes file not found: {saft_path}")

    if coa_path.exists():
        coa_entries = load_json(coa_path)
        logger.info(f"Loaded {len(coa_entries)} Chart of Accounts entries")
        accounting_data.extend(coa_entries)
    else:
        logger.warning(f"Chart of Accounts file not found: {coa_path}")

    if not accounting_data:
        logger.error("No accounting data found")
        return {}

    exporter = GlossaryExporter(
        output_dir=output_dir,
        domain="accounting",
        split_ratio=split_ratio,
    )

    stats = exporter.export(
        source_data=accounting_data,
        output_filename="accounting_glossary.jsonl",
    )

    return stats


def save_export_stats(stats: dict, output_dir: Path, export_type: str) -> None:
    """Save export statistics to metadata file."""
    metadata_dir = output_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    stats_file = metadata_dir / f"{export_type}_export_stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved export stats to {stats_file}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export Gold layer glossary training data"
    )
    parser.add_argument(
        "--silver-dir",
        type=str,
        default="data/silver",
        help="Silver layer directory (default: data/silver)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/gold",
        help="Gold layer output directory (default: data/gold)",
    )
    parser.add_argument(
        "--export-type",
        type=str,
        choices=["tax", "accounting", "all"],
        default="all",
        help="Export type: tax, accounting, or all (default: all)",
    )
    parser.add_argument(
        "--split-ratio",
        type=float,
        default=0.8,
        help="Train/val split ratio (default: 0.8)",
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    project_root = Path(__file__).parent.parent
    silver_dir = project_root / args.silver_dir
    output_dir = project_root / args.output_dir

    if not silver_dir.exists():
        logger.error(f"Silver directory not found: {silver_dir}")
        return 1

    all_stats = {}

    if args.export_type in ["tax", "all"]:
        tax_stats = export_tax_glossary(silver_dir, output_dir, args.split_ratio)
        all_stats["tax_glossary"] = tax_stats
        save_export_stats(tax_stats, output_dir, "tax_glossary")

    if args.export_type in ["accounting", "all"]:
        acc_stats = export_accounting_glossary(silver_dir, output_dir, args.split_ratio)
        all_stats["accounting_glossary"] = acc_stats
        save_export_stats(acc_stats, output_dir, "accounting_glossary")

    logger.info("\n" + "=" * 60)
    logger.info("EXPORT SUMMARY")
    logger.info("=" * 60)
    for export_name, stats in all_stats.items():
        logger.info(f"\n{export_name}:")
        logger.info(f"  Generated: {stats.get('total_generated', 0)}")
        logger.info(f"  Filtered: {stats.get('total_filtered', 0)}")
        logger.info(f"  Train samples: {stats.get('train_samples', 0)}")
        logger.info(f"  Val samples: {stats.get('val_samples', 0)}")
        logger.info(
            f"  Total: {stats.get('train_samples', 0) + stats.get('val_samples', 0)}"
        )

    logger.info("\n✓ Export complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
