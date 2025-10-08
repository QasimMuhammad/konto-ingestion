#!/usr/bin/env python3
"""
Test script for visualization tools.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from visualize_silver import SilverDataInspector
from generate_html_report import generate_html_report


def test_visualization():
    """Test the visualization tools."""
    silver_file = Path("data/silver/law_sections.json")

    if not silver_file.exists():
        print(f"Error: Silver file {silver_file} not found")
        print("Please run the Silver processing first:")
        print("  uv run process-to-silver")
        return 1

    print("🔍 Testing Silver data visualization...")

    # Test data inspector
    print("\n1. Testing SilverDataInspector...")
    inspector = SilverDataInspector(silver_file)

    print("\n2. Running summary analysis...")
    inspector.show_summary()

    print("\n3. Showing sample sections...")
    inspector.show_sample_sections(count=2)

    print("\n4. Running text analysis...")
    inspector.show_text_analysis(sample_size=50)

    print("\n5. Running quality analysis...")
    inspector.show_metadata_quality()

    print("\n6. Testing search functionality...")
    inspector.show_search_results("merverdiavgift", limit=3)

    print("\n7. Exporting sample data...")
    sample_file = Path("debug/sample_sections.json")
    inspector.export_sample_json(sample_file, count=5)

    print("\n8. Generating HTML report...")
    html_file = Path("debug/silver_report.html")
    generate_html_report(silver_file, html_file, sample_size=50)

    print("\n✅ Visualization test completed!")
    print("📁 Check these files:")
    print(f"  - {sample_file}")
    print(f"  - {html_file}")

    return 0


if __name__ == "__main__":
    sys.exit(test_visualization())
