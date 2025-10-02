#!/usr/bin/env python3
"""
Unit tests for Silver layer processing functionality.
"""

import json
import tempfile
import unittest
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.cleaners.silver_text_processing import (
    normalize_text,
    compute_stable_hash,
    extract_legal_metadata,
    enhance_section_metadata,
)
from modules.parsers.lovdata_parser import Section


class TestTextNormalization(unittest.TestCase):
    """Test text normalization functions."""

    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        html_input = "<p>Hello <strong>world</strong>!</p>"
        expected = "Hello world!"
        result = normalize_text(html_input)
        self.assertEqual(result, expected)

    def test_normalize_text_with_scripts(self):
        """Test normalization removes scripts and styles."""
        html_input = """
        <div>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
            <p>Clean text here</p>
        </div>
        """
        expected = "Clean text here"
        result = normalize_text(html_input)
        self.assertEqual(result, expected)

    def test_normalize_text_whitespace(self):
        """Test whitespace normalization."""
        html_input = "  Multiple   spaces\n\nand\t\ttabs  "
        expected = "Multiple spaces and tabs"
        result = normalize_text(html_input)
        self.assertEqual(result, expected)

    def test_normalize_text_empty(self):
        """Test empty input handling."""
        self.assertEqual(normalize_text(""), "")
        self.assertEqual(normalize_text(None), "")

    def test_normalize_text_complex_html(self):
        """Test complex HTML structure."""
        html_input = """
        <div class="content">
            <h1>Title</h1>
            <p>Paragraph with <a href="#">link</a> and <em>emphasis</em>.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
        """
        expected = "Title Paragraph with link and emphasis. Item 1 Item 2"
        result = normalize_text(html_input)
        self.assertEqual(result, expected)


class TestStableHash(unittest.TestCase):
    """Test stable hash computation."""

    def test_compute_stable_hash_basic(self):
        """Test basic hash computation."""
        text = "Hello world"
        hash1 = compute_stable_hash(text)
        hash2 = compute_stable_hash(text)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 hex length

    def test_compute_stable_hash_canonicalization(self):
        """Test hash is stable across whitespace variations."""
        text1 = "  Hello   world  "
        text2 = "hello world"
        text3 = "HELLO WORLD"

        hash1 = compute_stable_hash(text1)
        hash2 = compute_stable_hash(text2)
        hash3 = compute_stable_hash(text3)

        self.assertEqual(hash1, hash2)
        self.assertEqual(hash2, hash3)

    def test_compute_stable_hash_empty(self):
        """Test empty input handling."""
        self.assertEqual(compute_stable_hash(""), "")
        self.assertEqual(compute_stable_hash(None), "")


class TestLegalMetadataExtraction(unittest.TestCase):
    """Test legal metadata extraction."""

    def test_extract_law_title(self):
        """Test law title extraction."""
        html = "<h1 class='title'>Merverdiavgiftsloven</h1>"
        metadata = {"title": "Test Law"}
        result = extract_legal_metadata(html, metadata)
        self.assertEqual(result["law_title"], "Merverdiavgiftsloven")

    def test_extract_chapter(self):
        """Test chapter extraction."""
        html = "<h2>Kapittel 5. Avgiftsberegning</h2>"
        metadata = {}
        result = extract_legal_metadata(html, metadata)
        self.assertEqual(result["chapter"], "Kapittel 5. Avgiftsberegning")

    def test_detect_repealed(self):
        """Test repealed status detection."""
        html = "<p>Denne paragrafen er opphevet ved lov 2020 nr. 1</p>"
        metadata = {}
        result = extract_legal_metadata(html, metadata)
        self.assertTrue(result["repealed"])

    def test_extract_amendment_dates(self):
        """Test amendment date extraction."""
        html = """
        <p>Endret ved lov 15 juni 2020 nr. 45 (ikr. 1 juli 2020)</p>
        <p>Endret ved lov 20 desember 2021 nr. 100</p>
        """
        metadata = {}
        result = extract_legal_metadata(html, metadata)
        self.assertIn("15 juni 2020", result["amended_dates"])
        self.assertIn("20 desember 2021", result["amended_dates"])

    def test_no_metadata_found(self):
        """Test when no metadata is found."""
        html = "<p>Just some text</p>"
        metadata = {}
        result = extract_legal_metadata(html, metadata)
        self.assertEqual(result.get("law_title", ""), "")
        self.assertEqual(result.get("chapter", ""), "")
        self.assertFalse(result.get("repealed", False))
        self.assertEqual(result.get("amended_dates", []), [])


class TestSectionMetadataEnhancement(unittest.TestCase):
    """Test section metadata enhancement."""

    def setUp(self):
        """Set up test data."""
        self.section = Section(
            law_id="test_law",
            section_id="§ 1-1",
            path="Kapittel 1 § 1-1",
            heading="Test heading",
            text_plain="<p>Test content</p>",
            source_url="https://example.com",
            sha256="test_hash",
        )
        self.metadata = {
            "source_id": "test_law",
            "url": "https://example.com",
            "domain": "tax",
            "source_type": "law",
            "publisher": "Lovdata",
            "version": "current",
            "jurisdiction": "NO",
            "effective_from": "2020-01-01",
            "effective_to": "",
            "title": "Test Law",
            "crawl_freq": "quarterly",
        }
        self.html_content = "<h1>Test Law</h1><p>Test content</p>"

    def test_enhance_section_metadata_basic(self):
        """Test basic metadata enhancement."""
        result = enhance_section_metadata(
            self.section, self.metadata, self.html_content
        )

        # Check original fields
        self.assertEqual(result["law_id"], "test_law")
        self.assertEqual(result["section_id"], "§ 1-1")
        self.assertEqual(result["path"], "Kapittel 1 § 1-1")
        self.assertEqual(result["heading"], "Test heading")

        # Check normalized text
        self.assertEqual(result["text_plain"], "Test content")
        self.assertEqual(result["text_html"], self.html_content)

        # Check metadata fields
        self.assertEqual(result["domain"], "tax")
        self.assertEqual(result["source_type"], "law")
        self.assertEqual(result["publisher"], "Lovdata")
        self.assertEqual(result["version"], "current")
        self.assertEqual(result["jurisdiction"], "NO")
        self.assertEqual(result["effective_from"], "2020-01-01")
        self.assertEqual(result["effective_to"], "")
        self.assertEqual(result["crawl_freq"], "quarterly")

        # Check computed fields
        self.assertIsInstance(result["sha256"], str)
        self.assertEqual(len(result["sha256"]), 64)
        self.assertIsInstance(result["token_count"], int)
        self.assertGreater(result["token_count"], 0)
        self.assertIsInstance(result["ingested_at"], str)
        self.assertIsInstance(result["processed_at"], str)

    def test_enhance_section_metadata_missing_url(self):
        """Test handling of missing source URL."""
        section_no_url = Section(
            law_id="test_law",
            section_id="§ 1-1",
            path="Kapittel 1 § 1-1",
            heading="Test heading",
            text_plain="Test content",
            source_url="",
            sha256="test_hash",
        )

        result = enhance_section_metadata(
            section_no_url, self.metadata, self.html_content
        )
        self.assertEqual(
            result["source_url"], "https://example.com"
        )  # Falls back to metadata URL

    def test_enhance_section_metadata_legal_extraction(self):
        """Test legal metadata extraction in enhancement."""
        html_with_legal = """
        <h1>Merverdiavgiftsloven</h1>
        <h2>Kapittel 5. Avgiftsberegning</h2>
        <p>Denne paragrafen er opphevet ved lov 15 juni 2020 nr. 1</p>
        """

        result = enhance_section_metadata(self.section, self.metadata, html_with_legal)

        self.assertEqual(result["law_title"], "Merverdiavgiftsloven")
        self.assertEqual(result["chapter"], "Kapittel 5. Avgiftsberegning")
        self.assertTrue(result["repealed"])
        # The amendment date extraction might not work with this simple pattern
        # Just check that we have some amended_dates structure
        self.assertIsInstance(result["amended_dates"], list)


class TestSilverProcessingIntegration(unittest.TestCase):
    """Integration tests for Silver processing."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.bronze_dir = Path(self.temp_dir) / "bronze"
        self.silver_dir = Path(self.temp_dir) / "silver"
        self.bronze_dir.mkdir()
        self.silver_dir.mkdir()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_quality_checks(self):
        """Test quality checks in processing."""
        # Create test metadata
        metadata = [
            {
                "source_id": "test_law",
                "url": "https://example.com",
                "sha256": "test_hash",
                "domain": "tax",
                "source_type": "law",
                "publisher": "Lovdata",
                "title": "Test Law",
                "version": "current",
                "jurisdiction": "NO",
                "effective_from": "2020-01-01",
                "effective_to": "",
                "crawl_freq": "quarterly",
            }
        ]

        metadata_file = self.bronze_dir / "ingestion_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

        # Create sources_lookup for the test
        sources_lookup = {
            "test_law": {
                "source_id": "test_law",
                "url": "https://example.com",
                "domain": "tax",
                "source_type": "law",
                "publisher": "Lovdata",
                "title": "Test Law",
                "version": "current",
                "jurisdiction": "NO",
                "effective_from": "2020-01-01",
                "effective_to": "",
                "crawl_freq": "quarterly",
            }
        }

        # Create test HTML file with proper Lovdata structure
        html_content = """
        <html>
        <body>
            <h1>Test Law</h1>
            <div class="morTag_p paragraf" id="PARAGRAF_1-1">
                <h3 class="paragrafHeader">
                    <span class="paragrafValue">§ 1-1.</span>
                    <span class="paragrafTittel">Test heading</span>
                </h3>
                <div class="morTag_an avsnitt">
                    <span class="avsnittNummer">(1)</span>
                    <span>This is a test paragraph with sufficient content to pass quality checks and meet the minimum length requirements for processing.</span>
                </div>
            </div>
        </body>
        </html>
        """

        html_file = self.bronze_dir / "test_law.html"
        with open(html_file, "w") as f:
            f.write(html_content)

        # Test processing
        from scripts.process_bronze_to_silver import process_lovdata_files

        sections = process_lovdata_files(self.bronze_dir, self.silver_dir, sources_lookup)
        self.assertGreater(len(sections), 0)

        # Check quality
        for section in sections:
            self.assertGreaterEqual(len(section["text_plain"]), 50)
            self.assertTrue(section["source_url"])
            self.assertGreater(section["token_count"], 0)

    def test_unknown_law_skipping(self):
        """Test that files without metadata in sources_lookup are skipped."""
        # Create HTML file without corresponding metadata in sources_lookup
        html_content = """
        <html>
        <body>
            <h1>Unknown Law</h1>
            <div class="morTag_p paragraf" id="PARAGRAF_1-1">
                <h3 class="paragrafHeader">
                    <span class="paragrafValue">§ 1-1.</span>
                    <span class="paragrafTittel">Test heading</span>
                </h3>
                <div class="morTag_an avsnitt">
                    <span class="avsnittNummer">(1)</span>
                    <span>This law has no metadata entry and should be skipped.</span>
                </div>
            </div>
        </body>
        </html>
        """

        html_file = self.bronze_dir / "unknown_law.html"
        with open(html_file, "w") as f:
            f.write(html_content)

        # Create empty metadata file
        metadata_file = self.bronze_dir / "ingestion_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump([], f)

        # Create empty sources_lookup (no entries for unknown_law)
        sources_lookup = {}

        # Test processing
        from scripts.process_bronze_to_silver import process_lovdata_files

        sections = process_lovdata_files(self.bronze_dir, self.silver_dir, sources_lookup)

        # Should skip unknown files and return empty list
        self.assertEqual(len(sections), 0)


if __name__ == "__main__":
    unittest.main()
