#!/usr/bin/env python3
"""
Main entry point for Gold layer training data export.

Orchestrates export of glossaries, rule applications, and synthetic conversations
for LLM fine-tuning.
"""

import argparse
import json
import sys
from pathlib import Path

from modules.exporters.glossary_exporter import GlossaryExporter
from modules.exporters.rule_exporter import RuleExporter
from modules.exporters.synthetic_exporter import SyntheticExporter
from modules.exporters.utils import load_json
from modules.logger import logger
from modules.schemas import GoldTrainingSample


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Gold Layer Training Data Export")
    parser.add_argument(
        "command",
        choices=["glossary", "rules", "synthetic", "all", "validate", "eval"],
        help=(
            "Command: glossary (tax+accounting glossaries), "
            "rules (posting proposals), "
            "synthetic (conversations), "
            "all (run all exporters), "
            "validate (check JSONL), "
            "eval (run evaluation harness)"
        ),
    )
    parser.add_argument(
        "--silver-dir",
        type=Path,
        default=Path("data/silver"),
        help="Silver layer data directory",
    )
    parser.add_argument(
        "--gold-dir",
        type=Path,
        default=Path("data/gold"),
        help="Gold layer output directory",
    )
    parser.add_argument(
        "--split-ratio",
        type=float,
        default=0.8,
        help="Train/val split ratio (default: 0.8)",
    )
    parser.add_argument(
        "--export-type",
        choices=["tax", "accounting", "both"],
        default="both",
        help="For glossary: export type",
    )
    parser.add_argument(
        "--variations-per-rule",
        type=int,
        default=15,
        help="For rules: number of variations per rule",
    )
    parser.add_argument(
        "--conversations-per-template",
        type=int,
        default=250,
        help="For synthetic: conversations per template",
    )
    parser.add_argument(
        "--eval-dir",
        type=Path,
        default=Path("data/gold/eval"),
        help="For eval: evaluation dataset directory",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="mock",
        help="For eval: model name or checkpoint path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/eval_report.json"),
        help="For eval: output JSON file",
    )
    parser.add_argument(
        "--use-expected",
        action="store_true",
        help="For eval: use expected output as predicted (testing)",
    )

    return parser.parse_args()


def export_glossary(
    silver_dir: Path, gold_dir: Path, export_type: str, split_ratio: float
) -> dict:
    """Export glossary datasets."""
    logger.info("=" * 80)
    logger.info("EXPORTING GLOSSARY DATA")
    logger.info("=" * 80)

    stats_list = []

    if export_type in ["tax", "both"]:
        logger.info("\nExporting tax glossary...")
        exporter = GlossaryExporter(gold_dir, domain="tax", split_ratio=split_ratio)
        law_sections_data = load_json(silver_dir / "law_sections.json")
        law_sections = law_sections_data if isinstance(law_sections_data, list) else []
        stats = exporter.export(law_sections, "tax_glossary.jsonl")
        stats_list.append(("tax", stats))

        metadata_file = gold_dir / "metadata" / "tax_glossary_export_stats.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, "w") as f:
            json.dump(stats, f, indent=2)

    if export_type in ["accounting", "both"]:
        logger.info("\nExporting accounting glossary...")
        exporter = GlossaryExporter(
            gold_dir, domain="accounting", split_ratio=split_ratio
        )

        sources: list[dict] = []
        saft_path = silver_dir / "saft_v1_3_nodes.json"
        coa_path = silver_dir / "chart_of_accounts.json"

        if saft_path.exists():
            saft_data = load_json(saft_path)
            if isinstance(saft_data, list):
                sources.extend(saft_data)
        if coa_path.exists():
            coa_data = load_json(coa_path)
            if isinstance(coa_data, list):
                sources.extend(coa_data)

        stats = exporter.export(sources, "accounting_glossary.jsonl")
        stats_list.append(("accounting", stats))

        metadata_file = gold_dir / "metadata" / "accounting_glossary_export_stats.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, "w") as f:
            json.dump(stats, f, indent=2)

    logger.info("\n" + "=" * 80)
    logger.info("GLOSSARY EXPORT COMPLETE")
    logger.info("=" * 80)

    for export_name, stats in stats_list:
        logger.info(
            f"{export_name}: {stats['train_samples']} train + {stats['val_samples']} val"
        )

    return {"exports": stats_list}


def export_rules(
    silver_dir: Path, gold_dir: Path, split_ratio: float, variations_per_rule: int
) -> dict:
    """Export rule application datasets."""
    logger.info("=" * 80)
    logger.info("EXPORTING RULE APPLICATION DATA")
    logger.info("=" * 80)

    rules_data = load_json(silver_dir / "business_rules.json")
    rules = rules_data if isinstance(rules_data, list) else []
    logger.info(f"Loaded {len(rules)} business rules")

    exporter = RuleExporter(gold_dir, split_ratio)
    exporter.variations_per_rule = variations_per_rule

    stats = exporter.export(rules, "rule_application.jsonl")

    logger.info("\n" + "=" * 80)
    logger.info("RULE EXPORT COMPLETE")
    logger.info("=" * 80)
    logger.info(
        f"Generated: {stats['train_samples']} train + {stats['val_samples']} val"
    )

    return stats


def export_synthetic(
    silver_dir: Path,
    gold_dir: Path,
    split_ratio: float,
    conversations_per_template: int,
) -> dict:
    """Export synthetic conversation datasets."""
    logger.info("=" * 80)
    logger.info("EXPORTING SYNTHETIC CONVERSATIONS")
    logger.info("=" * 80)

    rules_data = load_json(silver_dir / "business_rules.json")
    rules = rules_data if isinstance(rules_data, list) else []
    logger.info(f"Loaded {len(rules)} business rules")

    exporter = SyntheticExporter(gold_dir, split_ratio, conversations_per_template)
    stats = exporter.export(rules, "synthetic_conversations.jsonl")

    logger.info("\n" + "=" * 80)
    logger.info("SYNTHETIC EXPORT COMPLETE")
    logger.info("=" * 80)
    logger.info(
        f"Generated: {stats['train_samples']} train + {stats['val_samples']} val"
    )

    return stats


def export_all(args: argparse.Namespace) -> dict:
    """Run all exporters in sequence."""
    logger.info("=" * 80)
    logger.info("GOLD LAYER EXPORT - ALL DATASETS")
    logger.info("=" * 80)

    all_stats = {}

    all_stats["glossary"] = export_glossary(
        args.silver_dir, args.gold_dir, "both", args.split_ratio
    )

    all_stats["rules"] = export_rules(
        args.silver_dir, args.gold_dir, args.split_ratio, args.variations_per_rule
    )

    all_stats["synthetic"] = export_synthetic(
        args.silver_dir,
        args.gold_dir,
        args.split_ratio,
        args.conversations_per_template,
    )

    total_train = sum(
        s.get("train_samples", 0)
        for s in [
            all_stats["rules"],
            all_stats["synthetic"],
        ]
    )
    glossary_stats = all_stats["glossary"]["exports"]
    total_train += sum(s[1].get("train_samples", 0) for s in glossary_stats)

    total_val = sum(
        s.get("val_samples", 0)
        for s in [
            all_stats["rules"],
            all_stats["synthetic"],
        ]
    )
    total_val += sum(s[1].get("val_samples", 0) for s in glossary_stats)

    combined_stats = {
        "total_samples": total_train + total_val,
        "train_samples": total_train,
        "val_samples": total_val,
        "exports": all_stats,
    }

    stats_file = args.gold_dir / "metadata" / "combined_export_stats.json"
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_file, "w") as f:
        json.dump(combined_stats, f, indent=2, ensure_ascii=False)

    logger.info("\n" + "=" * 80)
    logger.info("ALL EXPORTS COMPLETE")
    logger.info("=" * 80)
    logger.info(
        f"Total: {total_train} train + {total_val} val = {total_train + total_val}"
    )
    logger.info(f"Statistics saved to: {stats_file}")

    return combined_stats


def validate_samples(gold_dir: Path) -> int:
    """Validate all generated JSONL samples."""
    logger.info("=" * 80)
    logger.info("VALIDATING GOLD LAYER SAMPLES")
    logger.info("=" * 80)

    train_dir = gold_dir / "train"
    val_dir = gold_dir / "val"

    errors = 0

    for split_dir in [train_dir, val_dir]:
        if not split_dir.exists():
            continue

        for jsonl_file in split_dir.glob("*.jsonl"):
            logger.info(f"\nValidating: {jsonl_file.name}")

            try:
                with open(jsonl_file) as f:
                    for i, line in enumerate(f, 1):
                        try:
                            data = json.loads(line)
                            GoldTrainingSample(**data)
                        except Exception as e:
                            logger.error(f"  Line {i}: {e}")
                            errors += 1

                logger.info("  ✓ Valid!")

            except Exception as e:
                logger.error(f"  Failed to read file: {e}")
                errors += 1

    logger.info("\n" + "=" * 80)
    if errors == 0:
        logger.info("✓ ALL SAMPLES VALID")
    else:
        logger.error(f"✗ {errors} VALIDATION ERRORS")
    logger.info("=" * 80)

    return 0 if errors == 0 else 1


def run_eval(args: argparse.Namespace) -> int:
    """Run evaluation harness."""
    from scripts.eval_glossary import evaluate_samples, load_eval_samples, print_summary

    logger.info("=" * 80)
    logger.info("GOLD LAYER EVALUATION")
    logger.info("=" * 80)

    eval_files = list(args.eval_dir.glob("*_eval.jsonl"))
    if not eval_files:
        logger.error(f"No eval files found in {args.eval_dir}")
        return 1

    logger.info(f"Loading eval samples from: {args.eval_dir}")

    all_samples = []
    for eval_file in eval_files:
        samples = load_eval_samples(eval_file)
        logger.info(f"  {eval_file.name}: {len(samples)} samples")
        all_samples.extend(samples)

    logger.info(f"\nTotal eval samples: {len(all_samples)}\n")

    report = evaluate_samples(all_samples, args.model_name, args.use_expected)
    print_summary(report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"\nReport saved to: {args.output}")

    pass_rate = report["aggregate_metrics"]["pass_rate"]
    return 0 if pass_rate >= 0.90 else 1


def main() -> int:
    """Main entry point."""
    args = parse_args()

    try:
        if args.command == "glossary":
            export_glossary(
                args.silver_dir, args.gold_dir, args.export_type, args.split_ratio
            )
            return 0

        elif args.command == "rules":
            export_rules(
                args.silver_dir,
                args.gold_dir,
                args.split_ratio,
                args.variations_per_rule,
            )
            return 0

        elif args.command == "synthetic":
            export_synthetic(
                args.silver_dir,
                args.gold_dir,
                args.split_ratio,
                args.conversations_per_template,
            )
            return 0

        elif args.command == "all":
            export_all(args)
            return 0

        elif args.command == "validate":
            return validate_samples(args.gold_dir)

        elif args.command == "eval":
            return run_eval(args)

        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
