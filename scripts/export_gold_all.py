#!/usr/bin/env python3
"""
Orchestrate all Gold layer training data exports.

Runs all exporters in sequence and generates comprehensive statistics.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from modules.logger import logger


def run_exporter(script: str, args: list[str]) -> dict:
    """Run an exporter script and capture its output."""
    cmd = ["uv", "run", script] + args
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=Path.cwd()
        )
        logger.info(f"✓ {script} completed successfully")
        return {"success": True, "output": result.stdout, "error": None}
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {script} failed: {e.stderr}")
        return {"success": False, "output": e.stdout, "error": e.stderr}


def load_export_stats(metadata_dir: Path) -> dict:
    """Load export statistics from metadata files."""
    stats = {}

    for stat_file in metadata_dir.glob("*_export_stats.json"):
        try:
            with open(stat_file) as f:
                data = json.load(f)
                key = stat_file.stem.replace("_export_stats", "")
                stats[key] = data
        except Exception as e:
            logger.warning(f"Could not load {stat_file}: {e}")

    return stats


def count_jsonl_lines(file_path: Path) -> int:
    """Count lines in a JSONL file."""
    if not file_path.exists():
        return 0
    try:
        with open(file_path) as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def generate_combined_stats(gold_dir: Path) -> dict:
    """Generate combined statistics from all generated files."""
    train_dir = gold_dir / "train"
    val_dir = gold_dir / "val"
    metadata_dir = gold_dir / "metadata"

    train_files = list(train_dir.glob("*.jsonl"))

    dataset_stats = {}
    total_train = 0
    total_val = 0

    for train_file in train_files:
        dataset_name = train_file.stem
        val_file = val_dir / f"{dataset_name}.jsonl"

        train_count = count_jsonl_lines(train_file)
        val_count = count_jsonl_lines(val_file)

        dataset_stats[dataset_name] = {
            "train": train_count,
            "val": val_count,
            "total": train_count + val_count,
        }

        total_train += train_count
        total_val += val_count

    individual_stats = load_export_stats(metadata_dir)

    combined_stats = {
        "export_timestamp": datetime.now().isoformat(),
        "total_samples": total_train + total_val,
        "train_samples": total_train,
        "val_samples": total_val,
        "datasets": dataset_stats,
        "individual_exports": individual_stats,
    }

    return combined_stats


def export_all_gold_data(
    silver_dir: Path,
    gold_dir: Path,
    split_ratio: float = 0.8,
    variations_per_rule: int = 15,
    conversations_per_template: int = 250,
) -> dict:
    """
    Run all Gold layer exporters and generate combined statistics.

    Args:
        silver_dir: Path to silver layer data
        gold_dir: Path to gold layer output
        split_ratio: Train/val split ratio
        variations_per_rule: Number of variations per business rule
        conversations_per_template: Number of conversations per template

    Returns:
        Combined statistics dictionary
    """
    logger.info("=" * 80)
    logger.info("GOLD LAYER EXPORT ORCHESTRATOR")
    logger.info("=" * 80)
    logger.info(f"Silver directory: {silver_dir}")
    logger.info(f"Gold directory: {gold_dir}")
    logger.info(f"Split ratio: {split_ratio}")
    logger.info("")

    exporters = [
        {
            "name": "Glossary Exporter",
            "script": "scripts/export_gold_glossary.py",
            "args": [
                "--silver-dir",
                str(silver_dir),
                "--output-dir",
                str(gold_dir),
                "--split-ratio",
                str(split_ratio),
            ],
        },
        {
            "name": "Rule Application Exporter",
            "script": "scripts/export_gold_rules.py",
            "args": [
                "--silver-dir",
                str(silver_dir),
                "--output-dir",
                str(gold_dir),
                "--split-ratio",
                str(split_ratio),
                "--variations-per-rule",
                str(variations_per_rule),
            ],
        },
    ]

    results = []
    failed = []

    for exporter in exporters:
        logger.info("")
        logger.info(f"Running: {exporter['name']}")
        logger.info("-" * 80)

        result = run_exporter(exporter["script"], exporter["args"])
        results.append({"name": exporter["name"], **result})

        if not result["success"]:
            failed.append(exporter["name"])
            logger.error(f"Failed: {exporter['name']}")

    logger.info("")
    logger.info("=" * 80)
    logger.info("GENERATING COMBINED STATISTICS")
    logger.info("=" * 80)

    combined_stats = generate_combined_stats(gold_dir)

    stats_file = gold_dir / "metadata" / "combined_export_stats.json"
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_file, "w") as f:
        json.dump(combined_stats, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Statistics saved to: {stats_file}")
    logger.info("")

    logger.info("=" * 80)
    logger.info("EXPORT SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total samples:      {combined_stats['total_samples']:,}")
    logger.info(f"Training samples:   {combined_stats['train_samples']:,}")
    logger.info(f"Validation samples: {combined_stats['val_samples']:,}")
    logger.info("")

    logger.info("By Dataset:")
    for dataset, stats in combined_stats["datasets"].items():
        logger.info(
            f"  {dataset:30s}: {stats['train']:4d} train + {stats['val']:4d} val = {stats['total']:4d} total"
        )

    logger.info("")

    if failed:
        logger.warning(f"⚠️  Failed exporters: {', '.join(failed)}")
        logger.info("=" * 80)
        return {"success": False, "stats": combined_stats, "failed": failed}
    else:
        logger.info("✓ All exporters completed successfully!")
        logger.info("=" * 80)
        return {"success": True, "stats": combined_stats, "failed": []}


def main() -> None:
    """Main orchestrator script."""
    parser = argparse.ArgumentParser(description="Export all Gold layer training data")
    parser.add_argument(
        "--silver-dir",
        type=Path,
        default=Path("data/silver"),
        help="Directory containing Silver layer data",
    )
    parser.add_argument(
        "--gold-dir",
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
        help="Number of variations per business rule (default: 15)",
    )
    parser.add_argument(
        "--conversations-per-template",
        type=int,
        default=250,
        help="Number of conversations per template (default: 250)",
    )

    args = parser.parse_args()

    result = export_all_gold_data(
        args.silver_dir,
        args.gold_dir,
        args.split_ratio,
        args.variations_per_rule,
        args.conversations_per_template,
    )

    if not result["success"]:
        logger.error("Some exporters failed")
        sys.exit(1)

    logger.info("\n✓ Gold layer export complete!")


if __name__ == "__main__":
    main()
