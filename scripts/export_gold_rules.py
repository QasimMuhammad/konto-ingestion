#!/usr/bin/env python3
"""
Export Gold layer rule-based posting proposal training data.

Generates variations of business rules with different amounts, descriptions,
and contexts for LLM fine-tuning.
"""

import argparse
import json
from pathlib import Path

from modules.exporters.rule_exporter import RuleExporter
from modules.logger import logger


def load_json(file_path: Path) -> list[dict]:
    """Load JSON data from file."""
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def export_rule_samples(
    silver_dir: Path,
    output_dir: Path,
    split_ratio: float = 0.8,
    variations_per_rule: int = 15,
) -> dict:
    """
    Export rule-based posting proposals from business rules.

    Args:
        silver_dir: Path to silver layer data
        output_dir: Path to output directory for Gold layer
        split_ratio: Train/val split ratio (default: 0.8)
        variations_per_rule: Number of variations per rule (default: 15)

    Returns:
        Dictionary with export statistics
    """
    logger.info("=" * 80)
    logger.info("EXPORTING RULE APPLICATION TRAINING DATA")
    logger.info("=" * 80)

    rules_file = silver_dir / "business_rules.json"
    if not rules_file.exists():
        logger.error(f"Business rules file not found: {rules_file}")
        return {}

    rules = load_json(rules_file)
    logger.info(f"Loaded {len(rules)} business rules from {rules_file}")

    active_rules = [r for r in rules if r.get("is_active", True)]
    logger.info(f"Active rules: {len(active_rules)}")

    exporter = RuleExporter(output_dir, split_ratio)
    exporter.variations_per_rule = variations_per_rule

    logger.info(
        f"Generating {variations_per_rule} variations per rule "
        f"({len(active_rules) * variations_per_rule} total expected)"
    )

    stats = exporter.export(
        source_data=active_rules,
        output_filename="rule_application.jsonl",
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

    train_file = output_dir / "train" / "rule_application.jsonl"
    val_file = output_dir / "val" / "rule_application.jsonl"
    logger.info("Output files:")
    logger.info(f"  - {train_file}")
    logger.info(f"  - {val_file}")

    return stats


def main() -> None:
    """Main export script."""
    parser = argparse.ArgumentParser(
        description="Export rule-based posting proposal training data"
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
        "--variations-per-rule",
        type=int,
        default=15,
        help="Number of variations per rule (default: 15)",
    )

    args = parser.parse_args()

    export_rule_samples(
        args.silver_dir,
        args.output_dir,
        args.split_ratio,
        args.variations_per_rule,
    )


if __name__ == "__main__":
    main()
