"""
Data quality checker for comprehensive data quality assessment.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .validator import DataValidator, ValidationResult
from ..data_io import log


class QualityChecker:
    """Comprehensive data quality checker."""
    
    def __init__(self):
        self.validator = DataValidator()
        self.quality_metrics: Dict[str, Any] = {}
    
    def check_completeness(self, dataset: List[Dict[str, Any]], required_fields: List[str] = None) -> Dict[str, Any]:
        """Check data completeness."""
        if not dataset:
            return {"completeness_score": 0.0, "missing_fields": {}, "empty_records": 0}
        
        if required_fields is None:
            required_fields = ["source_url", "sha256", "domain", "publisher"]
        
        total_records = len(dataset)
        field_completeness = {}
        empty_records = 0
        
        # Check each required field
        for field in required_fields:
            non_empty_count = sum(1 for record in dataset if record.get(field) and str(record.get(field)).strip())
            completeness = (non_empty_count / total_records) * 100
            field_completeness[field] = {
                "completeness_percentage": completeness,
                "non_empty_count": non_empty_count,
                "empty_count": total_records - non_empty_count
            }
        
        # Count empty records
        for record in dataset:
            if not any(record.get(field) and str(record.get(field)).strip() for field in required_fields):
                empty_records += 1
        
        # Calculate overall completeness score
        overall_completeness = sum(field_completeness[field]["completeness_percentage"] for field in required_fields) / len(required_fields)
        
        return {
            "completeness_score": overall_completeness,
            "field_completeness": field_completeness,
            "empty_records": empty_records,
            "total_records": total_records
        }
    
    def check_consistency(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check data consistency."""
        if not dataset:
            return {"consistency_score": 100.0, "inconsistencies": []}
        
        inconsistencies = []
        
        # Check domain consistency
        domains = [record.get("domain") for record in dataset if record.get("domain")]
        unique_domains = set(domains)
        
        if len(unique_domains) > 1:
            inconsistencies.append({
                "type": "multi_domain",
                "description": f"Dataset contains multiple domains: {list(unique_domains)}",
                "severity": "warning",
                "affected_records": len(dataset)
            })
        
        # Check publisher consistency
        publishers = [record.get("publisher") for record in dataset if record.get("publisher")]
        unique_publishers = set(publishers)
        
        if len(unique_publishers) > 1:
            inconsistencies.append({
                "type": "multi_publisher",
                "description": f"Dataset contains multiple publishers: {list(unique_publishers)}",
                "severity": "info",
                "affected_records": len(dataset)
            })
        
        # Check for duplicate content
        seen_hashes = set()
        duplicates = []
        
        for i, record in enumerate(dataset):
            if "sha256" in record and record["sha256"]:
                if record["sha256"] in seen_hashes:
                    duplicates.append(i)
                else:
                    seen_hashes.add(record["sha256"])
        
        if duplicates:
            inconsistencies.append({
                "type": "duplicates",
                "description": f"Found {len(duplicates)} duplicate records",
                "severity": "warning",
                "affected_records": duplicates
            })
        
        # Calculate consistency score
        inconsistency_score = len(inconsistencies) * 10  # 10 points per inconsistency
        consistency_score = max(0, 100 - inconsistency_score)
        
        return {
            "consistency_score": consistency_score,
            "inconsistencies": inconsistencies,
            "duplicate_count": len(duplicates),
            "unique_domains": len(unique_domains),
            "unique_publishers": len(unique_publishers)
        }
    
    def check_accuracy(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check data accuracy."""
        if not dataset:
            return {"accuracy_score": 100.0, "accuracy_issues": []}
        
        accuracy_issues = []
        
        # Check URL validity
        invalid_urls = []
        for i, record in enumerate(dataset):
            if "source_url" in record and record["source_url"]:
                if not self._is_valid_url(record["source_url"]):
                    invalid_urls.append(i)
        
        if invalid_urls:
            accuracy_issues.append({
                "type": "invalid_urls",
                "description": f"Found {len(invalid_urls)} invalid URLs",
                "severity": "error",
                "affected_records": invalid_urls
            })
        
        # Check SHA256 validity
        invalid_hashes = []
        for i, record in enumerate(dataset):
            if "sha256" in record and record["sha256"]:
                if not self._is_valid_sha256(record["sha256"]):
                    invalid_hashes.append(i)
        
        if invalid_hashes:
            accuracy_issues.append({
                "type": "invalid_hashes",
                "description": f"Found {len(invalid_hashes)} invalid SHA256 hashes",
                "severity": "error",
                "affected_records": invalid_hashes
            })
        
        # Check domain validity
        invalid_domains = []
        valid_domains = ["tax", "accounting", "reporting"]
        
        for i, record in enumerate(dataset):
            if "domain" in record and record["domain"]:
                if record["domain"] not in valid_domains:
                    invalid_domains.append(i)
        
        if invalid_domains:
            accuracy_issues.append({
                "type": "invalid_domains",
                "description": f"Found {len(invalid_domains)} invalid domains",
                "severity": "error",
                "affected_records": invalid_domains
            })
        
        # Calculate accuracy score
        accuracy_penalty = len(invalid_urls) * 5 + len(invalid_hashes) * 10 + len(invalid_domains) * 5
        accuracy_score = max(0, 100 - accuracy_penalty)
        
        return {
            "accuracy_score": accuracy_score,
            "accuracy_issues": accuracy_issues,
            "invalid_url_count": len(invalid_urls),
            "invalid_hash_count": len(invalid_hashes),
            "invalid_domain_count": len(invalid_domains)
        }
    
    def check_timeliness(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check data timeliness."""
        if not dataset:
            return {"timeliness_score": 100.0, "timeliness_issues": []}
        
        timeliness_issues = []
        current_date = datetime.now()
        
        # Check last_updated fields
        outdated_records = []
        missing_timestamps = []
        
        for i, record in enumerate(dataset):
            if "last_updated" in record:
                if not record["last_updated"]:
                    missing_timestamps.append(i)
                else:
                    try:
                        # Parse timestamp (assuming ISO format)
                        record_date = datetime.fromisoformat(record["last_updated"].replace("Z", "+00:00"))
                        days_old = (current_date - record_date.replace(tzinfo=None)).days
                        
                        if days_old > 365:  # More than a year old
                            outdated_records.append(i)
                    except Exception:
                        # Invalid timestamp format
                        missing_timestamps.append(i)
            else:
                missing_timestamps.append(i)
        
        if outdated_records:
            timeliness_issues.append({
                "type": "outdated_data",
                "description": f"Found {len(outdated_records)} records older than 1 year",
                "severity": "warning",
                "affected_records": outdated_records
            })
        
        if missing_timestamps:
            timeliness_issues.append({
                "type": "missing_timestamps",
                "description": f"Found {len(missing_timestamps)} records without timestamps",
                "severity": "warning",
                "affected_records": missing_timestamps
            })
        
        # Calculate timeliness score
        timeliness_penalty = len(outdated_records) * 2 + len(missing_timestamps) * 3
        timeliness_score = max(0, 100 - timeliness_penalty)
        
        return {
            "timeliness_score": timeliness_score,
            "timeliness_issues": timeliness_issues,
            "outdated_count": len(outdated_records),
            "missing_timestamp_count": len(missing_timestamps)
        }
    
    def assess_overall_quality(self, dataset: List[Dict[str, Any]], required_fields: List[str] = None) -> Dict[str, Any]:
        """Assess overall data quality."""
        if not dataset:
            return {
                "overall_quality_score": 0.0,
                "quality_dimensions": {},
                "recommendations": ["Dataset is empty"]
            }
        
        # Run all quality checks
        completeness = self.check_completeness(dataset, required_fields)
        consistency = self.check_consistency(dataset)
        accuracy = self.check_accuracy(dataset)
        timeliness = self.check_timeliness(dataset)
        
        # Calculate overall quality score (weighted average)
        overall_score = (
            completeness["completeness_score"] * 0.3 +
            consistency["consistency_score"] * 0.25 +
            accuracy["accuracy_score"] * 0.25 +
            timeliness["timeliness_score"] * 0.2
        )
        
        # Generate recommendations
        recommendations = []
        
        if completeness["completeness_score"] < 80:
            recommendations.append("Improve data completeness by filling missing required fields")
        
        if consistency["consistency_score"] < 90:
            recommendations.append("Address data consistency issues")
        
        if accuracy["accuracy_score"] < 95:
            recommendations.append("Fix data accuracy issues (invalid URLs, hashes, domains)")
        
        if timeliness["timeliness_score"] < 85:
            recommendations.append("Update outdated data and ensure proper timestamps")
        
        if not recommendations:
            recommendations.append("Data quality is excellent - no major issues found")
        
        return {
            "overall_quality_score": overall_score,
            "quality_dimensions": {
                "completeness": completeness,
                "consistency": consistency,
                "accuracy": accuracy,
                "timeliness": timeliness
            },
            "recommendations": recommendations,
            "total_records": len(dataset),
            "assessment_timestamp": datetime.now().isoformat()
        }
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _is_valid_sha256(self, hash_str: str) -> bool:
        """Check if string is a valid SHA256 hash."""
        import re
        return bool(re.match(r'^[a-f0-9]{64}$', hash_str.lower()))
    
    def generate_quality_report(self, dataset: List[Dict[str, Any]], output_file: Optional[Path] = None) -> Dict[str, Any]:
        """Generate a comprehensive quality report."""
        quality_assessment = self.assess_overall_quality(dataset)
        
        report = {
            "quality_assessment": quality_assessment,
            "summary": {
                "overall_score": quality_assessment["overall_quality_score"],
                "grade": self._get_quality_grade(quality_assessment["overall_quality_score"]),
                "total_records": quality_assessment["total_records"],
                "assessment_date": quality_assessment["assessment_timestamp"]
            }
        }
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                log.info(f"Quality report saved to {output_file}")
            except Exception as e:
                log.error(f"Failed to save quality report: {e}")
        
        return report
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade."""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
