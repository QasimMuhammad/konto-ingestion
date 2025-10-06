#!/usr/bin/env python3
"""
Enhanced Silver layer validation script with comprehensive quality assessment.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

from modules.base_script import BaseScript, register_script
from modules.validation import DataValidator, QualityChecker
from modules.schemas import (
    LawSection, SpecNode, AmeldingRule, VatRate, 
    QualityReport, SilverMetadata
)
from modules.logger import logger


@register_script("validate-silver-enhanced")
class ValidateSilverEnhancedScript(BaseScript):
    """Enhanced script to validate Silver layer files with quality assessment."""
    
    def __init__(self):
        super().__init__("validate_silver_enhanced")
        self.validator = DataValidator()
        self.quality_checker = QualityChecker()
    
    def _execute(self) -> int:
        """Execute the enhanced Silver layer validation."""
        # Get silver directory
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        silver_dir = project_root / "data" / "silver"
        
        if not silver_dir.exists():
            logger.error(f"Silver directory not found: {silver_dir}")
            return 1
        
        logger.info(f"Enhanced validation of Silver layer files in: {silver_dir}")
        
        # Run enhanced validation
        results = self.validate_silver_directory_enhanced(silver_dir)
        
        # Print enhanced report
        self.print_enhanced_validation_report(results)
        
        # Return appropriate code
        if results["validation_failed"] or results["quality_issues"]:
            logger.error("Validation failed or quality issues found")
            return 1
        else:
            logger.info("All Silver layer files are valid with excellent quality!")
            return 0
    
    def validate_silver_directory_enhanced(self, silver_dir: Path) -> Dict[str, Any]:
        """Enhanced validation of Silver directory with quality assessment."""
        results = {
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "validation_failed": False,
            "quality_issues": False,
            "file_details": {},
            "overall_quality_score": 0.0,
            "quality_recommendations": []
        }
        
        # Define schema mapping
        schema_map = {
            "law_sections.json": LawSection,
            "tax_sections.json": LawSection,
            "accounting_sections.json": LawSection,
            "saft_v1_3_nodes.json": SpecNode,
            "amelding_rules.json": AmeldingRule,
            "rate_table.json": VatRate,
            "quality_report.json": QualityReport,
            "silver_metadata.json": SilverMetadata
        }
        
        json_files = list(silver_dir.glob("*.json"))
        results["total_files"] = len(json_files)
        
        all_datasets = []
        
        for json_file in json_files:
            logger.info(f"Validating {json_file.name}")
            
            file_result = self.validate_silver_file_enhanced(json_file, schema_map.get(json_file.name))
            results["file_details"][json_file.name] = file_result
            
            if file_result["is_valid"]:
                results["valid_files"] += 1
            else:
                results["invalid_files"] += 1
                results["validation_failed"] = True
            
            # Collect datasets for overall quality assessment
            if file_result["is_valid"] and file_result["data"]:
                all_datasets.extend(file_result["data"])
        
        # Overall quality assessment
        if all_datasets:
            overall_quality = self.quality_checker.assess_overall_quality(all_datasets)
            results["overall_quality_score"] = overall_quality["overall_quality_score"]
            results["quality_recommendations"] = overall_quality["recommendations"]
            
            if results["overall_quality_score"] < 80:
                results["quality_issues"] = True
        
        return results
    
    def validate_silver_file_enhanced(self, json_file: Path, schema_class) -> Dict[str, Any]:
        """Enhanced validation of a single Silver file."""
        result = {
            "file_name": json_file.name,
            "file_path": str(json_file),
            "is_valid": False,
            "record_count": 0,
            "validation_errors": [],
            "quality_score": 0.0,
            "quality_issues": [],
            "data": []
        }
        
        try:
            # Load JSON data
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Handle different data structures
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                if "records" in data:
                    records = data["records"]
                else:
                    records = [data]
            else:
                result["validation_errors"].append("Invalid JSON structure")
                return result
            
            result["record_count"] = len(records)
            result["data"] = records
            
            if not records:
                result["validation_errors"].append("No records found")
                return result
            
            # Validate with schema if available
            if schema_class:
                validation_result = self.validator.validate_dataset(records, schema_class)
                
                if validation_result.is_valid:
                    result["is_valid"] = True
                else:
                    result["validation_errors"].extend(validation_result.errors)
            
            # Quality assessment
            if records:
                quality_assessment = self.quality_checker.assess_overall_quality(records)
                result["quality_score"] = quality_assessment["overall_quality_score"]
                result["quality_issues"] = quality_assessment["recommendations"]
            
            # Additional validation for specific file types
            self.validate_file_specific_rules(json_file.name, records, result)
            
        except json.JSONDecodeError as e:
            result["validation_errors"].append(f"JSON decode error: {e}")
        except Exception as e:
            result["validation_errors"].append(f"Unexpected error: {e}")
        
        return result
    
    def validate_file_specific_rules(self, filename: str, records: List[Dict], result: Dict[str, Any]):
        """Validate file-specific business rules."""
        if filename == "rate_table.json":
            self.validate_vat_rates(records, result)
        elif filename in ["saft_v1_3_nodes.json"]:
            self.validate_saft_nodes(records, result)
        elif filename == "amelding_rules.json":
            self.validate_amelding_rules(records, result)
        elif filename in ["law_sections.json", "tax_sections.json", "accounting_sections.json"]:
            self.validate_law_sections(records, result)
    
    def validate_vat_rates(self, records: List[Dict], result: Dict[str, Any]):
        """Validate VAT rates specific rules."""
        for i, record in enumerate(records):
            # Check percentage is valid
            if "percentage" in record:
                try:
                    percentage = float(record["percentage"])
                    if not (0 <= percentage <= 100):
                        result["validation_errors"].append(f"Record {i}: Invalid percentage {percentage}")
                except (ValueError, TypeError):
                    result["validation_errors"].append(f"Record {i}: Invalid percentage format")
            
            # Check valid dates
            if "valid_from" in record and record["valid_from"]:
                if not self.is_valid_date(record["valid_from"]):
                    result["validation_errors"].append(f"Record {i}: Invalid valid_from date")
    
    def validate_saft_nodes(self, records: List[Dict], result: Dict[str, Any]):
        """Validate SAF-T nodes specific rules."""
        for i, record in enumerate(records):
            # Check node_path format
            if "node_path" in record and record["node_path"]:
                if not record["node_path"].startswith(("AuditFile.", "MasterFiles.", "GeneralLedgerEntries.")):
                    result["validation_errors"].append(f"Record {i}: Invalid node_path format")
            
            # Check cardinality format
            if "cardinality" in record and record["cardinality"]:
                if not self.is_valid_cardinality(record["cardinality"]):
                    result["validation_errors"].append(f"Record {i}: Invalid cardinality format")
    
    def validate_amelding_rules(self, records: List[Dict], result: Dict[str, Any]):
        """Validate A-melding rules specific rules."""
        valid_categories = ["form_guidance", "submission_deadlines", "business_logic", "data_structure"]
        
        for i, record in enumerate(records):
            # Check category validity
            if "category" in record and record["category"]:
                if record["category"] not in valid_categories:
                    result["validation_errors"].append(f"Record {i}: Invalid category '{record['category']}'")
    
    def validate_law_sections(self, records: List[Dict], result: Dict[str, Any]):
        """Validate law sections specific rules."""
        for i, record in enumerate(records):
            # Check section_id format
            if "section_id" in record and record["section_id"]:
                if not record["section_id"].startswith(("§", "PARAGRAF", "KAPITEL")):
                    result["validation_errors"].append(f"Record {i}: Invalid section_id format")
    
    def is_valid_date(self, date_str: str) -> bool:
        """Check if date string is valid."""
        try:
            from datetime import datetime
            datetime.fromisoformat(date_str)
            return True
        except (ValueError, TypeError):
            return False
    
    def is_valid_cardinality(self, cardinality: str) -> bool:
        """Check if cardinality string is valid."""
        valid_patterns = ["0..1", "0..*", "1..1", "1..*"]
        return cardinality in valid_patterns
    
    def print_enhanced_validation_report(self, results: Dict[str, Any]):
        """Print enhanced validation report."""
        logger.info("\n" + "=" * 80)
        logger.info("ENHANCED SILVER LAYER VALIDATION REPORT")
        logger.info("=" * 80)
        
        # Overall summary
        logger.info(f"Total files: {results['total_files']}")
        logger.info(f"Valid files: {results['valid_files']}")
        logger.info(f"Invalid files: {results['invalid_files']}")
        logger.info(f"Overall quality score: {results['overall_quality_score']:.1f}/100")
        
        if results['quality_recommendations']:
            logger.info(f"\nQuality recommendations:")
            for rec in results['quality_recommendations']:
                logger.info(f"  • {rec}")
        
        # File details
        logger.info(f"\nFile Details:")
        for filename, details in results['file_details'].items():
            status = "✅ VALID" if details['is_valid'] else "❌ INVALID"
            quality = f"Quality: {details['quality_score']:.1f}/100"
            records = f"Records: {details['record_count']}"
            
            logger.info(f"  {filename}: {status} | {quality} | {records}")
            
            if details['validation_errors']:
                logger.warning(f"    Errors: {len(details['validation_errors'])}")
                for error in details['validation_errors'][:3]:  # Show first 3 errors
                    logger.warning(f"      • {error}")
                if len(details['validation_errors']) > 3:
                    logger.warning(f"      • ... and {len(details['validation_errors']) - 3} more")
            
            if details['quality_issues']:
                logger.warning(f"    Quality issues: {len(details['quality_issues'])}")
                for issue in details['quality_issues'][:2]:  # Show first 2 issues
                    logger.warning(f"      • {issue}")
        
        logger.info("=" * 80)


def main():
    """Main entry point."""
    script = ValidateSilverEnhancedScript()
    return script.main()


if __name__ == "__main__":
    main()
