#!/usr/bin/env python3
"""
Silver layer validation script.
Validates all Silver JSON files against Pydantic schemas.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

from modules.base_script import BaseScript, register_script
from modules.schemas import LawSection, SpecNode, VatRate, AmeldingRule, QualityReport
from modules.data_io import log


def validate_law_sections(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate law sections JSON file."""
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            errors.append("Data must be a list of sections")
            return False, errors

        for i, item in enumerate(data):
            try:
                LawSection(**item)
            except Exception as e:
                errors.append(f"Record {i}: {str(e)}")

        log.info(f"Validated {len(data)} law sections from {file_path.name}")

    except Exception as e:
        errors.append(f"Failed to load file: {str(e)}")

    return len(errors) == 0, errors


def validate_spec_nodes(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate spec nodes JSON file."""
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            errors.append("Data must be a list of nodes")
            return False, errors

        for i, item in enumerate(data):
            try:
                SpecNode(**item)
            except Exception as e:
                errors.append(f"Record {i}: {str(e)}")

        log.info(f"Validated {len(data)} spec nodes from {file_path.name}")

    except Exception as e:
        errors.append(f"Failed to load file: {str(e)}")

    return len(errors) == 0, errors


def validate_vat_rates(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate VAT rates JSON file."""
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            errors.append("Data must be a list of rates")
            return False, errors

        for i, item in enumerate(data):
            try:
                VatRate(**item)
            except Exception as e:
                errors.append(f"Record {i}: {str(e)}")

        log.info(f"Validated {len(data)} VAT rates from {file_path.name}")

    except Exception as e:
        errors.append(f"Failed to load file: {str(e)}")

    return len(errors) == 0, errors


def validate_amelding_rules(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate A-meldingen rules JSON file."""
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            errors.append("Data must be a list of rules")
            return False, errors

        for i, item in enumerate(data):
            try:
                AmeldingRule(**item)
            except Exception as e:
                errors.append(f"Record {i}: {str(e)}")

        log.info(f"Validated {len(data)} A-meldingen rules from {file_path.name}")

    except Exception as e:
        errors.append(f"Failed to load file: {str(e)}")

    return len(errors) == 0, errors


def validate_quality_report(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate quality report JSON file."""
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        try:
            QualityReport(**data)
            log.info(f"Validated quality report from {file_path.name}")
        except Exception as e:
            errors.append(f"Quality report validation failed: {str(e)}")

    except Exception as e:
        errors.append(f"Failed to load file: {str(e)}")

    return len(errors) == 0, errors


def validate_silver_directory(silver_dir: Path) -> Dict[str, Any]:
    """Validate all Silver layer files."""
    results = {
        "total_files": 0,
        "valid_files": 0,
        "invalid_files": 0,
        "errors": [],
        "file_results": {},
    }

    # Define validation functions for different file types
    validators = {
        "law_sections.json": validate_law_sections,
        "tax_sections.json": validate_law_sections,
        "accounting_sections.json": validate_law_sections,
        "saft_v1_3_nodes.json": validate_spec_nodes,
        "rate_table.json": validate_vat_rates,
        "amelding_rules.json": validate_amelding_rules,
        "quality_report.json": validate_quality_report,
    }

    # Find all JSON files in silver directory
    json_files = list(silver_dir.glob("*.json"))
    results["total_files"] = len(json_files)

    for file_path in json_files:
        file_name = file_path.name
        results["file_results"][file_name] = {"valid": False, "errors": []}

        # Check if we have a validator for this file type
        if file_name in validators:
            is_valid, errors = validators[file_name](file_path)
            results["file_results"][file_name]["valid"] = is_valid
            results["file_results"][file_name]["errors"] = errors

            if is_valid:
                results["valid_files"] += 1
            else:
                results["invalid_files"] += 1
                results["errors"].extend([f"{file_name}: {error}" for error in errors])
        else:
            # Try to validate as generic JSON
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json.load(f)
                results["file_results"][file_name]["valid"] = True
                results["valid_files"] += 1
                log.info(f"Validated {file_name} as generic JSON")
            except Exception as e:
                results["file_results"][file_name]["valid"] = False
                results["file_results"][file_name]["errors"] = [str(e)]
                results["invalid_files"] += 1
                results["errors"].append(f"{file_name}: {str(e)}")

    return results


def print_validation_report(results: Dict[str, Any]) -> None:
    """Print validation report."""
    print("\n" + "=" * 60)
    print("SILVER LAYER VALIDATION REPORT")
    print("=" * 60)
    print(f"Total files: {results['total_files']}")
    print(f"Valid files: {results['valid_files']}")
    print(f"Invalid files: {results['invalid_files']}")
    print(f"Success rate: {results['valid_files'] / results['total_files'] * 100:.1f}%")

    if results["errors"]:
        print("\nERRORS:")
        print("-" * 40)
        for error in results["errors"]:
            print(f"  • {error}")

    print("\nFILE DETAILS:")
    print("-" * 40)
    for file_name, file_result in results["file_results"].items():
        status = "✓ VALID" if file_result["valid"] else "✗ INVALID"
        print(f"  {file_name}: {status}")
        if file_result["errors"]:
            for error in file_result["errors"]:
                print(f"    - {error}")

    print("=" * 60)


@register_script("validate-silver")
class ValidateSilverScript(BaseScript):
    """Script to validate Silver layer files."""

    def __init__(self):
        super().__init__("validate_silver")

    def _execute(self) -> int:
        """Execute the Silver layer validation."""
        # Get silver directory
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        silver_dir = project_root / "data" / "silver"

        if not silver_dir.exists():
            log.error(f"Silver directory not found: {silver_dir}")
            return 1

        log.info(f"Validating Silver layer files in: {silver_dir}")

        # Run validation
        results = validate_silver_directory(silver_dir)

        # Print report
        print_validation_report(results)

        # Return appropriate code
        if results["invalid_files"] > 0:
            log.error(f"Validation failed: {results['invalid_files']} invalid files")
            return 1
        else:
            log.info("All Silver layer files are valid!")
            return 0


def main():
    """Main entry point."""
    script = ValidateSilverScript()
    return script.main()


if __name__ == "__main__":
    main()
