#!/usr/bin/env python3
"""
Export JSON Schemas from Pydantic models.
Single source of truth for validation across tools and CI.
"""

import json
from pathlib import Path

from modules.logger import logger
from modules.schemas import (
    AmeldingRule,
    BusinessRule,
    ChartOfAccountsEntry,
    ExampleInput,
    ExampleOutput,
    LawSection,
    RuleAction,
    RuleCondition,
    RuleExample,
    SpecNode,
    VatRate,
)


def export_json_schemas(output_dir: Path | None = None) -> int:
    """
    Export JSON Schemas for all Pydantic models.

    Args:
        output_dir: Output directory for schemas (defaults to schemas/)

    Returns:
        0 on success, 1 on failure
    """
    if output_dir is None:
        output_dir = Path("schemas/")

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("EXPORTING JSON SCHEMAS")
    logger.info("=" * 80)

    schemas_to_export = {
        "BusinessRule": BusinessRule,
        "RuleCondition": RuleCondition,
        "RuleAction": RuleAction,
        "RuleExample": RuleExample,
        "ExampleInput": ExampleInput,
        "ExampleOutput": ExampleOutput,
        "ChartOfAccountsEntry": ChartOfAccountsEntry,
        "LawSection": LawSection,
        "VatRate": VatRate,
        "SpecNode": SpecNode,
        "AmeldingRule": AmeldingRule,
    }

    for name, model_class in schemas_to_export.items():
        try:
            schema = model_class.model_json_schema()  # type: ignore[attr-defined]
            output_path = output_dir / f"{name}.schema.json"

            with output_path.open("w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Exported: {output_path.name}")
        except Exception as e:
            logger.error(f"Failed to export {name}: {e}")
            return 1

    logger.info(f"\n✓ Total schemas exported: {len(schemas_to_export)} → {output_dir}")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(export_json_schemas())
