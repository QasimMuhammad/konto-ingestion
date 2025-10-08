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
            "node_id": "saft_audit_file_version",
            "node_path": "AuditFileVersion",
            "node_label": "Audit File Version",
            "node_level": 1,
            "parent_id": None,
            "data_type": "string",
            "description": "Version of the audit file",
            "cardinality": "1..1",
            "example_value": "1.30",
            "validation_rules": ["Required field"],
            "technical_details": ["Max length: 10"],
            "source_url": "https://skatteetaten.no",
            "sha256": "def456",
            "domain": "accounting",
            "source_type": "spec",
            "publisher": "Skatteetaten",
            "version": "1.3",
            "jurisdiction": "NO",
            "last_updated": datetime.now().isoformat(),
        }

        node = SpecNode(**node_data)
        self.assertEqual(node.node_path, "AuditFileVersion")
        self.assertEqual(node.data_type, "string")

    def test_spec_node_defaults(self):
        """Test SpecNode default values."""
        minimal_data = {
            "node_id": "test_node",
            "node_path": "TestNode",
            "node_label": "Test Node",
            "node_level": 0,
            "description": "Test description",
            "source_url": "https://test.com",
            "sha256": "test",
            "publisher": "Test",
            "last_updated": datetime.now().isoformat(),
        }

        node = SpecNode(**minimal_data)
        self.assertEqual(node.domain, "accounting")  # SpecNode defaults to accounting
        self.assertEqual(node.source_type, "spec")  # SpecNode defaults to "spec"
        self.assertEqual(node.jurisdiction, "NO")
        self.assertEqual(node.version, "1.3")
        self.assertIsNone(node.data_type)  # data_type is Optional and defaults to None
        self.assertIsNone(node.parent_id)  # parent_id is Optional and defaults to None
        self.assertIsNone(
            node.cardinality
        )  # cardinality is Optional and defaults to None


class TestVatRateSchema(unittest.TestCase):
    """Test VatRate schema validation."""

    def test_valid_vat_rate(self):
        """Test valid VatRate creation."""
        rate_data = {
            "rate_id": "vat_standard_25",
            "rate_label": "Standard VAT 25%",
            "rate_value": 25.0,
            "description": "Standard VAT rate",
            "effective_from": "2024-01-01",
            "effective_to": None,
            "source_url": "https://skatteetaten.no",
            "sha256": "ghi789",
            "domain": "tax",
            "source_type": "rates",
            "publisher": "Skatteetaten",
            "jurisdiction": "NO",
            "last_updated": datetime.now().isoformat(),
        }

        rate = VatRate(**rate_data)
        self.assertEqual(rate.rate_id, "vat_standard_25")
        self.assertEqual(rate.rate_value, 25.0)
        self.assertEqual(rate.rate_label, "Standard VAT 25%")

    def test_vat_rate_validation(self):
        """Test VatRate validation rules."""
        # Test that valid data creates a VatRate object
        vat_rate = VatRate(
            rate_id="vat_test",
            rate_label="Test VAT 25%",
            rate_value=25.0,
            description="Standard VAT rate",
            effective_from="2024-01-01",
            source_url="https://test.com",
            sha256="test",
            domain="tax",
            source_type="rates",
            publisher="Test",
            last_updated=datetime.now().isoformat(),
        )
        self.assertEqual(vat_rate.rate_id, "vat_test")
        self.assertEqual(vat_rate.rate_value, 25.0)

        # Test that any rate_id string is accepted (no validation constraints)
        vat_rate_any_kind = VatRate(
            rate_id="any_string_is_valid",
            rate_label="Test VAT 15%",
            rate_value=15.0,
            description="Test rate",
            effective_from="2024-01-01",
            source_url="https://test.com",
            sha256="test",
            domain="tax",
            source_type="rates",
            publisher="Test",
            last_updated=datetime.now().isoformat(),
        )
        self.assertEqual(vat_rate_any_kind.rate_id, "any_string_is_valid")

        # Test that high rate values are accepted (no validation constraints)
        vat_rate_high = VatRate(
            rate_id="vat_special",
            rate_label="Special VAT 150%",
            rate_value=150.0,  # > 100 - should be accepted
            description="Special rate",
            effective_from="2024-01-01",
            source_url="https://test.com",
            sha256="test",
            domain="tax",
            source_type="rates",
            publisher="Test",
            last_updated=datetime.now().isoformat(),
        )
        self.assertEqual(vat_rate_high.rate_value, 150.0)


class TestAmeldingRuleSchema(unittest.TestCase):
    """Test AmeldingRule schema validation."""

    def test_valid_amelding_rule(self):
        """Test valid AmeldingRule creation."""
        rule_data = {
            "rule_id": "rule_001",
            "category": "submission_deadlines",
            "subcategory": "monthly",
            "field_id": "field_001",
            "field_label": "Employee ID",
            "description": "Submit A-meldingen monthly",
            "data_type": "string",
            "cardinality": "1",
            "validation_rules": ["Employee ID must be 11 digits"],
            "example_value": "12345678901",
            "source_url": "https://altinn.no",
            "sha256": "jkl012",
            "domain": "reporting",
            "source_type": "spec",
            "publisher": "Altinn",
            "version": "1.0",
            "jurisdiction": "NO",
            "last_updated": datetime.now().isoformat(),
        }

        rule = AmeldingRule(**rule_data)
        self.assertEqual(rule.rule_id, "rule_001")
        self.assertEqual(rule.category, "submission_deadlines")
        self.assertEqual(rule.field_id, "field_001")

    def test_amelding_rule_validation(self):
        """Test AmeldingRule validation rules."""
        # Test that any category string is accepted (no validation constraints)
        rule = AmeldingRule(
            rule_id="test",
            category="any_category_is_valid",
            subcategory="test",
            field_id="test_field",
            field_label="Test Field",
            description="Test",
            source_url="https://test.com",
            sha256="test",
            publisher="Test",
            version="1.0",
            last_updated=datetime.now().isoformat(),
        )
        self.assertEqual(rule.category, "any_category_is_valid")


class TestQualityReportSchema(unittest.TestCase):
    """Test QualityReport schema validation."""

    def test_valid_quality_report(self):
        """Test valid QualityReport creation."""
        report_data = {
            "overall_score": 85.5,
            "completeness_score": 90.0,
            "consistency_score": 85.0,
            "accuracy_score": 88.0,
            "timeliness_score": 80.0,
            "total_records": 1000,
            "valid_records": 950,
            "issues": ["50 records with short text"],
            "recommendations": ["Improve data completeness"],
            "assessment_date": datetime.now().isoformat(),
        }

        report = QualityReport(**report_data)
        self.assertEqual(report.overall_score, 85.5)
        self.assertEqual(report.total_records, 1000)
        self.assertEqual(report.valid_records, 950)
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.assessment_date, report_data["assessment_date"])


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
