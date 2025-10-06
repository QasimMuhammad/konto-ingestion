#!/usr/bin/env python3
"""
Comprehensive Silver layer data analysis tool.
Analyzes all Silver layer files and provides detailed insights.
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.schemas import LawSection, SpecNode, VatRate, AmeldingRule


def load_json_file(file_path: Path):
    """Load JSON file with error handling."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def analyze_law_sections(data):
    """Analyze law sections data."""
    if not data:
        return {}

    analysis = {
        "total_sections": len(data),
        "domains": Counter(),
        "source_types": Counter(),
        "publishers": Counter(),
        "laws": Counter(),
        "avg_token_count": 0,
        "sections_with_metadata": 0,
        "repealed_sections": 0,
        "sections_by_chapter": defaultdict(int),
    }

    total_tokens = 0

    for section in data:
        # Basic counts
        analysis["domains"][section.get("domain", "unknown")] += 1
        analysis["source_types"][section.get("source_type", "unknown")] += 1
        analysis["publishers"][section.get("publisher", "unknown")] += 1
        analysis["laws"][section.get("law_id", "unknown")] += 1

        # Token count
        token_count = section.get("token_count", 0)
        total_tokens += token_count
        if token_count > 0:
            analysis["sections_with_metadata"] += 1

        # Legal metadata
        if section.get("repealed", False):
            analysis["repealed_sections"] += 1

        chapter = section.get("chapter", "")
        if chapter:
            analysis["sections_by_chapter"][chapter] += 1

    analysis["avg_token_count"] = total_tokens / len(data) if data else 0

    return analysis


def analyze_saft_nodes(data):
    """Analyze SAF-T nodes data."""
    if not data:
        return {}

    analysis = {
        "total_nodes": len(data),
        "data_types": Counter(),
        "cardinalities": Counter(),
        "complexity_levels": Counter(),
        "priority_levels": Counter(),
        "publishers": Counter(),
        "nodes_with_examples": 0,
        "nodes_with_validation_rules": 0,
        "nodes_with_business_rules": 0,
        "avg_technical_details": 0,
    }

    total_tech_details = 0

    for node in data:
        # Basic counts
        analysis["data_types"][node.get("data_type", "unknown")] += 1
        analysis["cardinalities"][node.get("cardinality", "unknown")] += 1
        analysis["complexity_levels"][node.get("complexity", "unknown")] += 1
        analysis["priority_levels"][node.get("priority", "unknown")] += 1
        analysis["publishers"][node.get("publisher", "unknown")] += 1

        # Content analysis
        if node.get("examples"):
            analysis["nodes_with_examples"] += 1
        if node.get("validation_rules"):
            analysis["nodes_with_validation_rules"] += 1
        if node.get("business_rules"):
            analysis["nodes_with_business_rules"] += 1

        tech_details = node.get("technical_details", [])
        total_tech_details += len(tech_details)

    analysis["avg_technical_details"] = total_tech_details / len(data) if data else 0

    return analysis


def analyze_vat_rates(data):
    """Analyze VAT rates data."""
    if not data:
        return {}

    analysis = {
        "total_rates": len(data),
        "kinds": Counter(),
        "categories": Counter(),
        "publishers": Counter(),
        "current_rates": 0,
        "rates_with_validity": 0,
        "rates_with_exceptions": 0,
        "avg_percentage": 0,
    }

    total_percentage = 0

    for rate in data:
        # Basic counts
        analysis["kinds"][rate.get("kind", "unknown")] += 1
        analysis["categories"][rate.get("category", "unknown")] += 1
        analysis["publishers"][rate.get("publisher", "unknown")] += 1

        # Status analysis
        if rate.get("is_current", False):
            analysis["current_rates"] += 1
        if rate.get("valid_from") or rate.get("valid_to"):
            analysis["rates_with_validity"] += 1
        if rate.get("exceptions"):
            analysis["rates_with_exceptions"] += 1

        # Percentage analysis
        percentage = rate.get("percentage", 0)
        total_percentage += percentage

    analysis["avg_percentage"] = total_percentage / len(data) if data else 0

    return analysis


def analyze_amelding_rules(data):
    """Analyze A-meldingen rules data."""
    if not data:
        return {}

    analysis = {
        "total_rules": len(data),
        "categories": Counter(),
        "priorities": Counter(),
        "complexity_levels": Counter(),
        "publishers": Counter(),
        "rules_with_requirements": 0,
        "rules_with_examples": 0,
        "rules_with_technical_details": 0,
        "rules_with_validation_rules": 0,
        "avg_requirements_per_rule": 0,
    }

    total_requirements = 0

    for rule in data:
        # Basic counts
        analysis["categories"][rule.get("category", "unknown")] += 1
        analysis["priorities"][rule.get("priority", "unknown")] += 1
        analysis["complexity_levels"][rule.get("complexity", "unknown")] += 1
        analysis["publishers"][rule.get("publisher", "unknown")] += 1

        # Content analysis
        if rule.get("requirements"):
            analysis["rules_with_requirements"] += 1
            total_requirements += len(rule["requirements"])
        if rule.get("examples"):
            analysis["rules_with_examples"] += 1
        if rule.get("technical_details"):
            analysis["rules_with_technical_details"] += 1
        if rule.get("validation_rules"):
            analysis["rules_with_validation_rules"] += 1

    analysis["avg_requirements_per_rule"] = (
        total_requirements / len(data) if data else 0
    )

    return analysis


def print_analysis_summary(analyses):
    """Print analysis summary."""
    print("=" * 80)
    print("SILVER LAYER DATA ANALYSIS SUMMARY")
    print("=" * 80)

    total_records = 0
    for name, analysis in analyses.items():
        if analysis:
            if "total_sections" in analysis:
                total_records += analysis["total_sections"]
            elif "total_nodes" in analysis:
                total_records += analysis["total_nodes"]
            elif "total_rates" in analysis:
                total_records += analysis["total_rates"]
            elif "total_rules" in analysis:
                total_records += analysis["total_rules"]

    print(f"Total Records: {total_records:,}")
    print()

    for name, analysis in analyses.items():
        if not analysis:
            continue

        print(f"--- {name.upper().replace('_', ' ')} ---")

        if "total_sections" in analysis:
            print(f"  Sections: {analysis['total_sections']:,}")
            print(f"  Avg Tokens: {analysis['avg_token_count']:.1f}")
            print(f"  With Metadata: {analysis['sections_with_metadata']:,}")
            print(f"  Repealed: {analysis['repealed_sections']:,}")

        elif "total_nodes" in analysis:
            print(f"  Nodes: {analysis['total_nodes']:,}")
            print(f"  With Examples: {analysis['nodes_with_examples']:,}")
            print(
                f"  With Validation Rules: {analysis['nodes_with_validation_rules']:,}"
            )
            print(f"  With Business Rules: {analysis['nodes_with_business_rules']:,}")
            print(f"  Avg Technical Details: {analysis['avg_technical_details']:.1f}")

        elif "total_rates" in analysis:
            print(f"  Rates: {analysis['total_rates']:,}")
            print(f"  Current: {analysis['current_rates']:,}")
            print(f"  With Validity: {analysis['rates_with_validity']:,}")
            print(f"  Avg Percentage: {analysis['avg_percentage']:.1f}%")

        elif "total_rules" in analysis:
            print(f"  Rules: {analysis['total_rules']:,}")
            print(f"  With Requirements: {analysis['rules_with_requirements']:,}")
            print(f"  With Examples: {analysis['rules_with_examples']:,}")
            print(
                f"  With Technical Details: {analysis['rules_with_technical_details']:,}"
            )
            print(f"  Avg Requirements: {analysis['avg_requirements_per_rule']:.1f}")

        print()


def print_detailed_analysis(analyses):
    """Print detailed analysis."""
    print("=" * 80)
    print("DETAILED ANALYSIS")
    print("=" * 80)

    for name, analysis in analyses.items():
        if not analysis:
            continue

        print(f"\n--- {name.upper().replace('_', ' ')} DETAILS ---")

        # Print top categories for each type
        for key in [
            "domains",
            "source_types",
            "publishers",
            "laws",
            "data_types",
            "cardinalities",
            "complexity_levels",
            "priority_levels",
            "kinds",
            "categories",
            "priorities",
        ]:
            if key in analysis and analysis[key]:
                print(f"\n  Top {key.replace('_', ' ').title()}:")
                for item, count in analysis[key].most_common(5):
                    print(f"    {item}: {count:,}")


def validate_schemas(data_dir: Path):
    """Validate all Silver data against schemas."""
    print("=" * 80)
    print("SCHEMA VALIDATION")
    print("=" * 80)

    validation_results = {}

    # Test each file type
    test_files = [
        ("law_sections.json", LawSection),
        ("tax_sections.json", LawSection),
        ("accounting_sections.json", LawSection),
        ("saft_v1_3_nodes.json", SpecNode),
        ("rate_table.json", VatRate),
        ("amelding_rules.json", AmeldingRule),
    ]

    for filename, schema_class in test_files:
        file_path = data_dir / filename
        if not file_path.exists():
            print(f"  {filename}: File not found")
            continue

        data = load_json_file(file_path)
        if not data:
            print(f"  {filename}: Failed to load")
            continue

        errors = []
        valid_count = 0

        for i, item in enumerate(data):
            try:
                schema_class(**item)
                valid_count += 1
            except Exception as e:
                errors.append(f"Record {i}: {str(e)}")

        validation_results[filename] = {
            "total": len(data),
            "valid": valid_count,
            "errors": len(errors),
            "error_details": errors[:5],  # Show first 5 errors
        }

        success_rate = (valid_count / len(data)) * 100 if data else 0
        status = "✅" if success_rate == 100 else "❌"
        print(
            f"  {status} {filename}: {valid_count}/{len(data)} valid ({success_rate:.1f}%)"
        )

        if errors:
            print(f"    First error: {errors[0]}")

    return validation_results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze Silver layer data")
    parser.add_argument(
        "--data-dir", default="data/silver", help="Silver data directory"
    )
    parser.add_argument(
        "--detailed", action="store_true", help="Show detailed analysis"
    )
    parser.add_argument("--validate", action="store_true", help="Validate schemas")
    parser.add_argument("--export", help="Export analysis to JSON file")

    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist")
        sys.exit(1)

    # Load all data files
    data_files = {
        "law_sections": load_json_file(data_dir / "law_sections.json"),
        "tax_sections": load_json_file(data_dir / "tax_sections.json"),
        "accounting_sections": load_json_file(data_dir / "accounting_sections.json"),
        "saft_nodes": load_json_file(data_dir / "saft_v1_3_nodes.json"),
        "vat_rates": load_json_file(data_dir / "rate_table.json"),
        "amelding_rules": load_json_file(data_dir / "amelding_rules.json"),
    }

    # Analyze each dataset
    analyses = {}
    analyses["law_sections"] = analyze_law_sections(data_files["law_sections"])
    analyses["tax_sections"] = analyze_law_sections(data_files["tax_sections"])
    analyses["accounting_sections"] = analyze_law_sections(
        data_files["accounting_sections"]
    )
    analyses["saft_nodes"] = analyze_saft_nodes(data_files["saft_nodes"])
    analyses["vat_rates"] = analyze_vat_rates(data_files["vat_rates"])
    analyses["amelding_rules"] = analyze_amelding_rules(data_files["amelding_rules"])

    # Print results
    print_analysis_summary(analyses)

    if args.detailed:
        print_detailed_analysis(analyses)

    if args.validate:
        validation_results = validate_schemas(data_dir)

    if args.export:
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "analyses": analyses,
            "validation_results": validation_results if args.validate else None,
        }

        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        print(f"\nAnalysis exported to {args.export}")


if __name__ == "__main__":
    main()
