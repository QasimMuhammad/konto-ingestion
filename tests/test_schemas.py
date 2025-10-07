#!/usr/bin/env python3
"""
Unit tests for Pydantic schemas.
"""

import unittest
from datetime import datetime

from modules.schemas import AmeldingRule, LawSection, QualityReport, SpecNode, VatRate


class TestLawSectionSchema(unittest.TestCase):
    """Test LawSection schema validation."""

    def test_valid_law_section(self):
        """Test valid LawSection creation."""
        section_data = {
            "law_id": "mva_law_1999",
            "section_id": "§ 8-1",
            "path": "Kapittel 8 § 8-1",
            "heading": "Fradrag for merverdiavgift",
            "text_plain": "This is the section text content.",
            "source_url": "https://lovdata.no",
            "sha256": "abc123",
            "domain": "tax",
            "source_type": "law",
            "publisher": "Lovdata",
            "jurisdiction": "NO",
            "is_current": True,
            "effective_from": "2020-01-01",
            "effective_to": None,
            "last_updated": datetime.now().isoformat(),
            "section_label": "§ 8-1",
            "version": "current",
            "law_title": "Merverdiavgiftsloven",
            "chapter": "Kapittel 8",
            "chapter_no": "8",
        }

        section = LawSection(**section_data)
        self.assertEqual(section.law_id, "mva_law_1999")
        self.assertEqual(section.section_id, "§ 8-1")
        self.assertEqual(section.domain, "tax")

    def test_law_section_validation_errors(self):
        """Test LawSection validation errors."""
        # Missing required fields
        with self.assertRaises(Exception):
            LawSection(
                law_id="test",
                section_id="§ 1",
                path="Test",
                heading="Test",
                text_plain="Test",
                source_url="https://test.com",
                sha256="test",
            )


class TestSpecNodeSchema(unittest.TestCase):
    """Test SpecNode schema validation."""

    def test_valid_spec_node(self):
        """Test valid SpecNode creation."""
        node_data = {
            "spec": "SAF-T",
            "version": "1.30",
            "node_path": "AuditFileVersion",
            "cardinality": "1..1",
            "description": "Version of the audit file",
            "source_url": "https://skatteetaten.no",
            "sha256": "def456",
            "domain": "tax",
            "source_type": "specification",
            "publisher": "Skatteetaten",
            "jurisdiction": "NO",
            "is_current": True,
            "data_type": "string",
            "format": "String",
            "validation_rules": ["Required field"],
            "business_rules": ["Must be current version"],
            "examples": ["1.30"],
            "dependencies": [],
            "technical_details": ["Max length: 10"],
            "last_updated": datetime.now().isoformat(),
        }

        node = SpecNode(**node_data)
        self.assertEqual(node.node_path, "AuditFileVersion")
        self.assertEqual(node.data_type, "string")

    def test_spec_node_defaults(self):
        """Test SpecNode default values."""
        minimal_data = {
            "node_path": "TestNode",
            "cardinality": "1..1",
            "description": "Test description",
            "source_url": "https://test.com",
            "sha256": "test",
            "publisher": "Test",
            "is_current": True,
            "last_updated": datetime.now().isoformat(),
        }

        node = SpecNode(**minimal_data)
        self.assertEqual(node.domain, "reporting")  # SpecNode defaults to reporting
        self.assertEqual(node.source_type, "spec")  # SpecNode defaults to "spec"
        self.assertEqual(node.jurisdiction, "NO")
        self.assertEqual(node.data_type, "string")
        self.assertIsNone(node.format)  # format is Optional and defaults to None
        self.assertIsNone(node.priority)  # priority is Optional and defaults to None
        self.assertIsNone(
            node.complexity
        )  # complexity is Optional and defaults to None


class TestVatRateSchema(unittest.TestCase):
    """Test VatRate schema validation."""

    def test_valid_vat_rate(self):
        """Test valid VatRate creation."""
        rate_data = {
            "kind": "standard",
            "value": "25%",
            "percentage": 25.0,
            "valid_from": "2024-01-01",
            "valid_to": None,
            "description": "Standard VAT rate",
            "source_url": "https://skatteetaten.no",
            "sha256": "ghi789",
            "domain": "tax",
            "source_type": "rates",
            "publisher": "Skatteetaten",
            "jurisdiction": "NO",
            "is_current": True,
            "category": "general_goods",
            "applies_to": ["Most goods and services"],
            "exceptions": ["Food products"],
            "notes": "Main VAT rate",
            "last_updated": datetime.now().isoformat(),
        }

        rate = VatRate(**rate_data)
        self.assertEqual(rate.kind, "standard")
        self.assertEqual(rate.percentage, 25.0)
        self.assertEqual(rate.category, "general_goods")

    def test_vat_rate_validation(self):
        """Test VatRate validation rules."""
        # Test that valid data creates a VatRate object
        vat_rate = VatRate(
            kind="standard",
            percentage=25.0,
            description="Standard VAT rate",
            source_url="https://test.com",
            sha256="test",
            publisher="Test",
            is_current=True,
            category="test",
            last_updated=datetime.now().isoformat(),
        )
        self.assertEqual(vat_rate.kind, "standard")
        self.assertEqual(vat_rate.percentage, 25.0)

        # Test that any kind string is accepted (no validation constraints)
        vat_rate_any_kind = VatRate(
            kind="any_string_is_valid",
            percentage=15.0,
            description="Test rate",
            source_url="https://test.com",
            sha256="test",
            publisher="Test",
            is_current=True,
            category="test",
            last_updated=datetime.now().isoformat(),
        )
        self.assertEqual(vat_rate_any_kind.kind, "any_string_is_valid")

        # Test that high percentage values are accepted (no validation constraints)
        vat_rate_high = VatRate(
            kind="special",
            percentage=150.0,  # > 100 - should be accepted
            description="Special rate",
            source_url="https://test.com",
            sha256="test",
            publisher="Test",
            is_current=True,
            category="test",
            last_updated=datetime.now().isoformat(),
        )
        self.assertEqual(vat_rate_high.percentage, 150.0)


class TestAmeldingRuleSchema(unittest.TestCase):
    """Test AmeldingRule schema validation."""

    def test_valid_amelding_rule(self):
        """Test valid AmeldingRule creation."""
        rule_data = {
            "rule_id": "rule_001",
            "title": "Monthly Submission",
            "description": "Submit A-meldingen monthly",
            "category": "submission_deadlines",
            "applies_to": ["employers"],
            "requirements": ["Submit by 5th of month"],
            "examples": ["January submission due Feb 5th"],
            "source_url": "https://altinn.no",
            "sha256": "jkl012",
            "domain": "reporting",
            "source_type": "amelding_overview",
            "publisher": "Altinn",
            "jurisdiction": "NO",
            "is_current": True,
            "priority": "high",
            "complexity": "medium",
            "technical_details": ["XML format required"],
            "validation_rules": ["Employee ID must be 11 digits"],
            "field_mappings": {"employee_id": "personnummer"},
            "business_rules": ["Must include all employees"],
            "last_updated": datetime.now().isoformat(),
        }

        rule = AmeldingRule(**rule_data)
        self.assertEqual(rule.rule_id, "rule_001")
        self.assertEqual(rule.category, "submission_deadlines")
        self.assertEqual(rule.priority, "high")

    def test_amelding_rule_validation(self):
        """Test AmeldingRule validation rules."""
        # Test that any category string is accepted (no validation constraints)
        rule = AmeldingRule(
            rule_id="test",
            title="Test",
            description="Test",
            category="any_category_is_valid",
            source_url="https://test.com",
            sha256="test",
            publisher="Test",
            is_current=True,
            last_updated=datetime.now().isoformat(),
        )
        self.assertEqual(rule.category, "any_category_is_valid")


class TestQualityReportSchema(unittest.TestCase):
    """Test QualityReport schema validation."""

    def test_valid_quality_report(self):
        """Test valid QualityReport creation."""
        report_data = {
            "total_processed": 1000,
            "total_saved": 950,
            "rejected_short_text": 50,
            "validation_issues": 0,
            "total_tokens": 150000,
            "domains": {
                "tax": {"count": 500, "tokens": 75000},
                "accounting": {"count": 300, "tokens": 45000},
                "reporting": {"count": 200, "tokens": 30000},
            },
            "source_types": {"law": 800, "specification": 200},
            "publishers": {"Lovdata": 600, "Skatteetaten": 400},
            "quality_metrics": {
                "avg_token_count": 150.5,
                "sections_with_metadata": 950,
                "validation_errors": 0,
            },
            "last_updated": datetime.now().isoformat(),
        }

        report = QualityReport(**report_data)
        self.assertEqual(report.total_processed, 1000)
        self.assertEqual(report.domains["tax"]["count"], 500)
        # QualityReport has last_updated field
        self.assertEqual(report.last_updated, report_data["last_updated"])


class TestSchemaSerialization(unittest.TestCase):
    """Test schema serialization to/from JSON."""

    def test_law_section_serialization(self):
        """Test LawSection JSON serialization."""
        section = LawSection(
            law_id="test",
            section_id="§ 1",
            path="Test",
            heading="Test",
            text_plain="Test content",
            source_url="https://test.com",
            sha256="test",
            domain="tax",
            source_type="law",
            publisher="Test",
            jurisdiction="NO",
            is_current=True,
            last_updated=datetime.now().isoformat(),
            section_label="§ 1",
            version="current",
            law_title="Test Law",
            chapter="Test Chapter",
            chapter_no="1",
        )

        # Test to dict
        section_dict = section.model_dump()
        self.assertIsInstance(section_dict, dict)
        self.assertEqual(section_dict["law_id"], "test")

        # Test to JSON
        section_json = section.model_dump_json()
        self.assertIsInstance(section_json, str)

        # Test from dict
        section_from_dict = LawSection(**section_dict)
        self.assertEqual(section_from_dict.law_id, "test")

    def test_schema_export(self):
        """Test schema export functionality."""
        # Test that schemas can be exported
        law_schema = LawSection.model_json_schema()
        self.assertIsInstance(law_schema, dict)
        self.assertIn("properties", law_schema)

        spec_schema = SpecNode.model_json_schema()
        self.assertIsInstance(spec_schema, dict)
        self.assertIn("properties", spec_schema)


if __name__ == "__main__":
    unittest.main()
