#!/usr/bin/env python3
"""
Export Gold layer synthetic conversation training data.

Generates multi-turn conversations using templates and business rules.
"""

import argparse
import json
from pathlib import Path

from modules.exporters.synthetic_exporter import SyntheticExporter
from modules.logger import logger


def load_json(file_path: Path) -> list[dict]:
    """Load JSON data from file."""
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def export_synthetic_conversations(
    silver_dir: Path,
    output_dir: Path,
    split_ratio: float = 0.8,
    conversations_per_template: int = 250,
) -> dict:
    """
    Export synthetic conversation samples from templates and business rules.

    Args:
        silver_dir: Path to silver layer data
        output_dir: Path to output directory for Gold layer
        split_ratio: Train/val split ratio (default: 0.8)
        conversations_per_template: Number of conversations per template (default: 250)

    Returns:
        Dictionary with export statistics
    """
    logger.info("=" * 80)
    logger.info("EXPORTING SYNTHETIC CONVERSATION TRAINING DATA")
    logger.info("=" * 80)

    rules_file = silver_dir / "business_rules.json"
    if not rules_file.exists():
        logger.error(f"Business rules file not found: {rules_file}")
        return {}

    rules = load_json(rules_file)
    logger.info(f"Loaded {len(rules)} business rules from {rules_file}")

    active_rules = [r for r in rules if r.get("is_active", True)]
    logger.info(f"Active rules: {len(active_rules)}")

    exporter = SyntheticExporter(output_dir, split_ratio, conversations_per_template)

    logger.info(
        f"Generating {conversations_per_template} conversations per template (6 templates)"
    )

    stats = exporter.export(
        source_data=active_rules,
        output_filename="synthetic_conversations.jsonl",
    )

    logger.info("=" * 80)
    logger.info("EXPORT COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total samples: {stats.get('total_filtered', 0)}")
    logger.info(f"Train samples: {stats.get('train_samples', 0)}")
    logger.info(f"Val samples: {stats.get('val_samples', 0)}")
    logger.info(f"Duplicates removed: {stats.get('duplicates_removed', 0)}")
    logger.info(f"Quality issues: {stats.get('quality_issues', 0)}")
    logger.info("")

    train_file = output_dir / "train" / "synthetic_conversations.jsonl"
    val_file = output_dir / "val" / "synthetic_conversations.jsonl"
    logger.info("Output files:")
    logger.info(f"  - {train_file}")
    logger.info(f"  - {val_file}")

    return stats


def main() -> None:
    """Main export script."""
    parser = argparse.ArgumentParser(
        description="Export synthetic conversation training data"
    )
    parser.add_argument(
        "--silver-dir",
        type=Path,
        default=Path("data/silver"),
        help="Directory containing Silver layer data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/gold"),
        help="Output directory for Gold layer data",
    )
    parser.add_argument(
        "--split-ratio",
        type=float,
        default=0.8,
        help="Train/val split ratio (default: 0.8)",
    )
    parser.add_argument(
        "--conversations-per-template",
        type=int,
        default=250,
        help="Number of conversations per template (default: 250)",
    )

    args = parser.parse_args()

    export_synthetic_conversations(
        args.silver_dir,
        args.output_dir,
        args.split_ratio,
        args.conversations_per_template,
    )


if __name__ == "__main__":
    main()
