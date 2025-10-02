#!/usr/bin/env python3
"""
Debug visualization tool for Silver layer data.
Provides various ways to inspect and visualize the processed legal sections.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.data_io import log


class SilverDataInspector:
    """Tool for inspecting and visualizing Silver layer data."""

    def __init__(self, silver_file: Path):
        """Initialize with Silver data file."""
        self.silver_file = silver_file
        self.data: List[Dict[str, Any]] = []
        self.load_data()

    def load_data(self) -> None:
        """Load Silver data from JSON file."""
        try:
            with open(self.silver_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            log.info(f"Loaded {len(self.data)} sections from {self.silver_file}")
        except Exception as e:
            log.error(f"Failed to load data: {e}")
            sys.exit(1)

    def show_summary(self) -> None:
        """Display high-level summary statistics."""
        print("\n" + "=" * 60)
        print("📊 SILVER DATA SUMMARY")
        print("=" * 60)

        # Basic stats
        print(f"Total sections: {len(self.data):,}")

        # Domain breakdown
        domains = Counter(section.get("domain", "unknown") for section in self.data)
        print("\nDomains:")
        for domain, count in domains.most_common():
            print(f"  {domain}: {count:,} sections")

        # Source types
        source_types = Counter(
            section.get("source_type", "unknown") for section in self.data
        )
        print("\nSource types:")
        for stype, count in source_types.most_common():
            print(f"  {stype}: {count:,} sections")

        # Publishers
        publishers = Counter(
            section.get("publisher", "unknown") for section in self.data
        )
        print("\nPublishers:")
        for publisher, count in publishers.most_common():
            print(f"  {publisher}: {count:,} sections")

        # Token statistics
        token_counts = [section.get("token_count", 0) for section in self.data]
        if token_counts:
            print("\nToken statistics:")
            print(f"  Total tokens: {sum(token_counts):,}")
            print(f"  Average per section: {sum(token_counts) / len(token_counts):.1f}")
            print(f"  Min tokens: {min(token_counts)}")
            print(f"  Max tokens: {max(token_counts)}")

        # Repealed sections
        repealed_count = sum(
            1 for section in self.data if section.get("repealed", False)
        )
        print(
            f"\nRepealed sections: {repealed_count:,} ({repealed_count / len(self.data) * 100:.1f}%)"
        )

    def show_sample_sections(
        self, count: int = 3, domain: Optional[str] = None
    ) -> None:
        """Display sample sections with full metadata."""
        print("\n" + "=" * 60)
        print(f"📋 SAMPLE SECTIONS ({count} examples)")
        if domain:
            print(f"Filtered by domain: {domain}")
        print("=" * 60)

        # Filter by domain if specified
        filtered_data = self.data
        if domain:
            filtered_data = [s for s in self.data if s.get("domain") == domain]
            print(f"Found {len(filtered_data)} sections in domain '{domain}'")

        # Show samples
        for i, section in enumerate(filtered_data[:count]):
            print(f"\n--- SECTION {i + 1} ---")
            print(f"Law ID: {section.get('law_id', 'N/A')}")
            print(f"Section ID: {section.get('section_id', 'N/A')}")
            print(f"Path: {section.get('path', 'N/A')}")
            print(f"Heading: {section.get('heading', 'N/A')}")
            print(f"Domain: {section.get('domain', 'N/A')}")
            print(f"Source Type: {section.get('source_type', 'N/A')}")
            print(f"Publisher: {section.get('publisher', 'N/A')}")
            print(f"Version: {section.get('version', 'N/A')}")
            print(f"Repealed: {section.get('repealed', False)}")
            print(f"Token Count: {section.get('token_count', 0)}")
            print(
                f"Source URL: {section.get('source_url', 'N/A')[:80]}..."
                if section.get("source_url")
                else "N/A"
            )

            # Show text preview
            text_plain = section.get("text_plain", "")
            if text_plain:
                preview = (
                    text_plain[:200] + "..." if len(text_plain) > 200 else text_plain
                )
                print(f"Text Preview: {preview}")

            # Show legal metadata
            if section.get("amended_dates"):
                print(f"Amendment Dates: {section.get('amended_dates', [])}")

    def show_text_analysis(self, sample_size: int = 100) -> None:
        """Analyze text content patterns."""
        print("\n" + "=" * 60)
        print(f"📝 TEXT ANALYSIS (sample of {sample_size} sections)")
        print("=" * 60)

        # Sample data for analysis
        sample_data = (
            self.data[:sample_size] if len(self.data) > sample_size else self.data
        )

        # Text length analysis
        text_lengths = [len(section.get("text_plain", "")) for section in sample_data]
        if text_lengths:
            print("Text length statistics:")
            print(f"  Average: {sum(text_lengths) / len(text_lengths):.0f} chars")
            print(f"  Min: {min(text_lengths)} chars")
            print(f"  Max: {max(text_lengths)} chars")

        # Common words analysis
        all_text = " ".join(section.get("text_plain", "") for section in sample_data)
        words = all_text.lower().split()
        word_freq = Counter(words)

        print("\nMost common words (top 20):")
        for word, count in word_freq.most_common(20):
            if len(word) > 3:  # Skip short words
                print(f"  {word}: {count}")

        # Section ID patterns
        section_ids = [section.get("section_id", "") for section in sample_data]
        section_patterns = Counter()
        for sid in section_ids:
            if "§" in sid:
                section_patterns["paragraph"] += 1
            elif "KAPITTEL" in sid.upper():
                section_patterns["chapter"] += 1
            elif "ARTIKKEL" in sid.upper():
                section_patterns["article"] += 1
            else:
                section_patterns["other"] += 1

        print("\nSection ID patterns:")
        for pattern, count in section_patterns.items():
            print(f"  {pattern}: {count}")

    def show_metadata_quality(self) -> None:
        """Analyze metadata completeness and quality."""
        print("\n" + "=" * 60)
        print("🔍 METADATA QUALITY ANALYSIS")
        print("=" * 60)

        total = len(self.data)

        # Check completeness of key fields
        fields_to_check = [
            "source_url",
            "sha256",
            "domain",
            "source_type",
            "publisher",
            "version",
            "jurisdiction",
            "law_title",
            "token_count",
        ]

        print("Field completeness:")
        for field in fields_to_check:
            non_empty = sum(1 for section in self.data if section.get(field))
            percentage = (non_empty / total) * 100
            print(f"  {field}: {non_empty:,}/{total:,} ({percentage:.1f}%)")

        # Check for empty source URLs
        empty_urls = sum(1 for section in self.data if not section.get("source_url"))
        print(
            f"\nSections without source URL: {empty_urls:,} ({empty_urls / total * 100:.1f}%)"
        )

        # Check for very short text
        short_text = sum(
            1 for section in self.data if len(section.get("text_plain", "")) < 50
        )
        print(
            f"Sections with very short text (<50 chars): {short_text:,} ({short_text / total * 100:.1f}%)"
        )

        # Check amendment dates
        with_amendments = sum(
            1 for section in self.data if section.get("amended_dates")
        )
        print(
            f"Sections with amendment dates: {with_amendments:,} ({with_amendments / total * 100:.1f}%)"
        )

    def export_sample_json(self, output_file: Path, count: int = 10) -> None:
        """Export a sample of sections to a smaller JSON file for inspection."""
        sample_data = self.data[:count]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)

        print(f"\n📁 Exported {count} sections to {output_file}")

    def search_sections(
        self, query: str, field: str = "text_plain"
    ) -> List[Dict[str, Any]]:
        """Search sections by text content."""
        results = []
        query_lower = query.lower()

        for section in self.data:
            field_content = section.get(field, "")
            if isinstance(field_content, str) and query_lower in field_content.lower():
                results.append(section)

        return results

    def show_search_results(
        self, query: str, field: str = "text_plain", limit: int = 5
    ) -> None:
        """Display search results."""
        results = self.search_sections(query, field)

        print("\n" + "=" * 60)
        print(f"🔍 SEARCH RESULTS for '{query}' in {field}")
        print(f"Found {len(results)} matches (showing first {limit})")
        print("=" * 60)

        for i, section in enumerate(results[:limit]):
            print(f"\n--- MATCH {i + 1} ---")
            print(f"Law ID: {section.get('law_id', 'N/A')}")
            print(f"Section ID: {section.get('section_id', 'N/A')}")
            print(f"Domain: {section.get('domain', 'N/A')}")

            # Show context around the match
            field_content = section.get(field, "")
            if field_content:
                query_pos = field_content.lower().find(query.lower())
                if query_pos != -1:
                    start = max(0, query_pos - 100)
                    end = min(len(field_content), query_pos + len(query) + 100)
                    context = field_content[start:end]
                    print(f"Context: ...{context}...")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Visualize Silver layer data")
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        default=Path("data/silver/law_sections.json"),
        help="Path to Silver JSON file",
    )
    parser.add_argument(
        "--summary", "-s", action="store_true", help="Show summary statistics"
    )
    parser.add_argument(
        "--sample", "-n", type=int, default=3, help="Number of sample sections to show"
    )
    parser.add_argument("--domain", "-d", type=str, help="Filter by domain")
    parser.add_argument(
        "--text-analysis", "-t", action="store_true", help="Show text analysis"
    )
    parser.add_argument(
        "--quality", "-q", action="store_true", help="Show metadata quality analysis"
    )
    parser.add_argument("--export", "-e", type=Path, help="Export sample to JSON file")
    parser.add_argument("--search", type=str, help="Search for text in sections")
    parser.add_argument(
        "--search-field",
        default="text_plain",
        help="Field to search in (default: text_plain)",
    )
    parser.add_argument("--all", "-a", action="store_true", help="Run all analyses")

    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File {args.file} not found")
        sys.exit(1)

    inspector = SilverDataInspector(args.file)

    if args.all or args.summary:
        inspector.show_summary()

    if args.all or args.sample:
        inspector.show_sample_sections(args.sample, args.domain)

    if args.all or args.text_analysis:
        inspector.show_text_analysis()

    if args.all or args.quality:
        inspector.show_metadata_quality()

    if args.export:
        inspector.export_sample_json(args.export, 10)

    if args.search:
        inspector.show_search_results(args.search, args.search_field)


if __name__ == "__main__":
    main()
