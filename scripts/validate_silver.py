#!/usr/bin/env python3
"""
Silver layer validation script with quality assessment.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from modules.simple_validation import validate_silver_data as simple_validate
from modules.schemas import (
    LawSection,
    SpecNode,
    AmeldingRule,
    VatRate,
)
from modules.logger import logger


def parse_args():
    parser = argparse.ArgumentParser(description="Validate Silver layer data")
    parser.add_argument(
        "--silver-dir",
        type=str,
        default="data/silver",
        help="Silver directory path (default: data/silver)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for quality report (optional)",
    )
    return parser.parse_args()


def validate_silver_data(silver_dir: Path) -> Dict[str, Any]:
    """Validate Silver layer data with quality assessment."""

    results: dict[str, Any] = {
        "total_files": 0,
        "valid_files": 0,
        "invalid_files": 0,
        "validation_failed": False,
        "quality_issues": False,
        "file_details": {},
        "overall_quality_score": 0.0,
        "quality_recommendations": [],
    }

    # Define schema mapping
    schema_map = {
        "law_sections.json": LawSection,
        "saft_v1_3_nodes.json": SpecNode,
        "amelding_rules.json": AmeldingRule,
        "rate_table.json": VatRate,
    }

    # Check each expected file
    for filename, schema_class in schema_map.items():
        file_path = silver_dir / filename
        results["total_files"] += 1

        if not file_path.exists():
            logger.warning(f"Missing file: {filename}")
            results["invalid_files"] += 1
            results["validation_failed"] = True
            results["file_details"][filename] = {
                "status": "missing",
                "errors": ["File not found"],
                "quality_score": 0.0,
            }
            continue

        try:
            # Load and validate file
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.error(
                    f"Invalid format in {filename}: expected list, got {type(data)}"
                )
                results["invalid_files"] += 1
                results["validation_failed"] = True
                results["file_details"][filename] = {
                    "status": "invalid",
                    "errors": ["Invalid JSON format"],
                    "quality_score": 0.0,
                }
                continue

            # Validate each item using Pydantic
            validation_errors = []
            for i, item in enumerate(data):
                try:
                    schema_class(**item)
                except Exception as e:
                    validation_errors.append(f"Item {i}: {str(e)}")

            if validation_errors:
                logger.error(
                    f"Validation errors in {filename}: {len(validation_errors)} errors"
                )
                results["invalid_files"] += 1
                results["validation_failed"] = True
                results["file_details"][filename] = {
                    "status": "invalid",
                    "errors": validation_errors[:5],  # Show first 5 errors
                    "quality_score": 0.0,
                }
            else:
                # Run simple quality assessment
                quality_result = simple_validate(data)
                results["valid_files"] += 1
                results["file_details"][filename] = {
                    "status": "valid",
                    "errors": [],
                    "quality_score": quality_result.get("quality_score", 0.0),
                    "quality_issues": quality_result.get("issues", []),
                }

                # Track overall quality
                if quality_result.get("issues"):
                    results["quality_issues"] = True
                    results["quality_recommendations"].extend(
                        quality_result.get("recommendations", [])
                    )

        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            results["invalid_files"] += 1
            results["validation_failed"] = True
            results["file_details"][filename] = {
                "status": "error",
                "errors": [str(e)],
                "quality_score": 0.0,
            }

    # Calculate overall quality score
    if results["valid_files"] > 0:
        total_quality = sum(
            details.get("quality_score", 0.0)
            for details in results["file_details"].values()
            if details.get("status") == "valid"
        )
        results["overall_quality_score"] = total_quality / results["valid_files"]

    return results


def print_validation_report(results: Dict[str, Any]) -> None:
    """Print validation report."""
    logger.info("\n" + "=" * 60)
    logger.info("SILVER LAYER VALIDATION REPORT")
    logger.info("=" * 60)

    # Summary
    logger.info(f"\nTotal Files: {results['total_files']}")
    logger.info(f"Valid Files: {results['valid_files']}")
    logger.info(f"Invalid Files: {results['invalid_files']}")
    logger.info(f"Overall Quality Score: {results['overall_quality_score']:.2f}/10")

    # File details
    logger.info("\nFile Details:")
    for filename, details in results["file_details"].items():
        status = details["status"]
        quality_score = details.get("quality_score", 0.0)

        if status == "valid":
            logger.info(f"✅ {filename}: Valid (Quality: {quality_score:.2f}/10)")
        elif status == "invalid":
            logger.error(
                f"❌ {filename}: Invalid ({len(details.get('errors', []))} errors)"
            )
            for error in details.get("errors", [])[:3]:  # Show first 3
                logger.error(f"   - {error}")
        elif status == "missing":
            logger.warning(f"⚠️  {filename}: Missing")
        elif status == "error":
            logger.error(
                f"❌ {filename}: Error - {details.get('errors', ['Unknown'])[0]}"
            )

    # Quality recommendations
    if results["quality_recommendations"]:
        logger.info("\nQuality Recommendations:")
        for rec in set(results["quality_recommendations"]):  # Unique recommendations
            logger.info(f"  • {rec}")

    logger.info("\n" + "=" * 60)


def main():
    """Main entry point for the validation script."""
    args = parse_args()
    silver_dir = Path(args.silver_dir)

    # Ensure silver_dir is absolute or relative to project root
    if not silver_dir.is_absolute():
        project_root = Path(__file__).parent.parent
        silver_dir = project_root / silver_dir

    results = validate_silver_data(silver_dir)

    if args.output:
        output_path = Path(args.output)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Quality report saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save quality report to {output_path}: {e}")
            return 1

    print_validation_report(results)

    if results["validation_failed"]:
        logger.error("Validation failed - data integrity issues found")
        return 1
    else:
        logger.info("All Silver layer files are valid!")
        if results["quality_issues"]:
            logger.warning("Some quality improvements recommended but not blocking")
        return 0


if __name__ == "__main__":
    sys.exit(main())
