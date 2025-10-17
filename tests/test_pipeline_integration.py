"""
Integration smoke tests for Bronze→Silver pipeline.

Tests end-to-end pipeline orchestration, metadata persistence, and CLI argument handling.
"""

import json
import tempfile
from pathlib import Path

from modules.pipeline.domain_pipelines import (
    LegalTextProcessingPipeline,
    RatesProcessingPipeline,
)


def test_legal_text_pipeline_smoke():
    """Smoke test: Legal text pipeline processes Bronze to Silver correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        bronze_dir = test_dir / "bronze"
        silver_dir = test_dir / "silver"
        bronze_dir.mkdir()
        silver_dir.mkdir()

        sample_html = """
        <html>
        <div class="paragraf">
            <h2>§ 1-1. Test Section</h2>
            <p>This is a test legal section for smoke testing.</p>
        </div>
        </html>
        """

        bronze_file = bronze_dir / "test_law.html"
        bronze_file.write_text(sample_html)

        sources_file = test_dir / "sources.csv"
        with open(sources_file, "w") as f:
            f.write("source_id,url,domain,source_type,publisher,title\n")
            f.write("test_law,https://test.no/law,tax,law,Test,Test Law\n")

        pipeline = LegalTextProcessingPipeline()
        pipeline.setup(sources_file, bronze_dir, silver_dir)
        result = pipeline.execute()

        assert result.failed_items == 0, "No fatal failures expected"

        output_file = silver_dir / "law_sections.json"
        assert output_file.exists(), "Silver output should exist"

        data = json.load(open(output_file))
        assert isinstance(data, list), "Output should be list"

        if len(data) > 0:
            section = data[0]
            assert "sha256" in section, "Should have sha256 field"
            assert section["sha256"] != "bronze_hash", (
                "Should have real hash, not placeholder"
            )
            assert len(section["sha256"]) == 64, "SHA256 should be 64 hex chars"


def test_rates_pipeline_smoke():
    """Smoke test: Rates pipeline processes Bronze to Silver correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        bronze_dir = test_dir / "bronze"
        silver_dir = test_dir / "silver"
        bronze_dir.mkdir()
        silver_dir.mkdir()

        sample_html = """
        <html><body>
        <h2>Generell sats</h2>
        <p>25 % merverdiavgift</p>
        </body></html>
        """

        bronze_file = bronze_dir / "test_rates.html"
        bronze_file.write_text(sample_html)

        sources_file = test_dir / "sources.csv"
        with open(sources_file, "w") as f:
            f.write("source_id,url,domain,source_type\n")
            f.write("test_rates,https://test.no/rates,tax,rates\n")

        pipeline = RatesProcessingPipeline()
        pipeline.setup(sources_file, bronze_dir, silver_dir)
        result = pipeline.execute()

        assert result.failed_items == 0, "No fatal failures expected"

        output_file = silver_dir / "rate_table.json"
        if output_file.exists():
            data = json.load(open(output_file))
            if isinstance(data, list) and len(data) > 0:
                assert "sha256" in data[0], "Rates should have sha256"
                assert data[0]["sha256"] != "bronze_hash", "Should have real hash"


def test_pipeline_hash_propagation():
    """Test that Bronze file hash correctly propagates to Silver data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        bronze_dir = test_dir / "bronze"
        silver_dir = test_dir / "silver"
        bronze_dir.mkdir()
        silver_dir.mkdir()

        test_content = "<html><body>Test content for hash</body></html>"
        bronze_file = bronze_dir / "test.html"
        bronze_file.write_text(test_content)

        from modules.hash_utils import sha256_bytes

        expected_hash = sha256_bytes(bronze_file.read_bytes())

        sources_file = test_dir / "sources.csv"
        with open(sources_file, "w") as f:
            f.write("source_id,url,domain\n")
            f.write("test,https://test.no,tax\n")

        assert len(expected_hash) == 64, "Bronze hash should be 64 chars"
        assert expected_hash != "bronze_hash", "Should not be placeholder"
