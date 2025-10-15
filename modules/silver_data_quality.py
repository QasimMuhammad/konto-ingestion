"""
Silver layer data quality validation.
Validates data quality aspects like URLs, hashes, domains, and generates quality scores.
"""

from typing import Dict, List, Any
from datetime import datetime
import re
from urllib.parse import urlparse

MAX_SHOWN_ERRORS = 5
MAX_QUALITY_SCORE = 10
QUALITY_SCORE_EXCELLENT = 8
QUALITY_SCORE_ACCEPTABLE = 6


def validate_silver_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simple validation for Silver layer data.

    Args:
        data: List of data records to validate

    Returns:
        Dictionary with validation results
    """
    if not data:
        return {
            "is_valid": False,
            "quality_score": 0.0,
            "issues": ["Dataset is empty"],
            "recommendations": ["Add data to the dataset"],
        }

    return _validate_data_content(data)


def _validate_data_content(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate the content of the data."""
    issues = []
    recommendations = []

    required_fields = ["source_url", "sha256", "domain", "publisher"]
    missing_fields = []

    for i, record in enumerate(data):
        for field in required_fields:
            if field not in record or not record[field]:
                missing_fields.append(f"Record {i} missing {field}")

    if missing_fields:
        issues.extend(missing_fields[:MAX_SHOWN_ERRORS])
        recommendations.append("Fill in missing required fields")

    quality_issues = []

    invalid_urls = 0
    for record in data:
        if "source_url" in record and record["source_url"]:
            if not _is_valid_url(record["source_url"]):
                invalid_urls += 1

    if invalid_urls > 0:
        quality_issues.append(f"Found {invalid_urls} invalid URLs")
        recommendations.append("Fix invalid URLs")

    invalid_hashes = 0
    for record in data:
        if "sha256" in record and record["sha256"]:
            if not _is_valid_sha256(record["sha256"]):
                invalid_hashes += 1

    if invalid_hashes > 0:
        quality_issues.append(f"Found {invalid_hashes} invalid SHA256 hashes")
        recommendations.append("Fix invalid SHA256 hashes")

    invalid_domains = 0
    valid_domains = {"tax", "accounting", "reporting"}
    for record in data:
        if "domain" in record and record["domain"]:
            if record["domain"] not in valid_domains:
                invalid_domains += 1

    if invalid_domains > 0:
        quality_issues.append(f"Found {invalid_domains} invalid domains")
        recommendations.append("Use valid domains: tax, accounting, reporting")

    total_issues = len(issues) + len(quality_issues)
    max_issues = len(data) * 2
    quality_score = (
        max(0, MAX_QUALITY_SCORE - (total_issues / max_issues) * MAX_QUALITY_SCORE)
        if max_issues > 0
        else MAX_QUALITY_SCORE
    )

    issues.extend(quality_issues)

    if not recommendations:
        if quality_score >= QUALITY_SCORE_EXCELLENT:
            recommendations.append("Data quality is good")
        elif quality_score >= QUALITY_SCORE_ACCEPTABLE:
            recommendations.append(
                "Data quality is acceptable with minor improvements needed"
            )
        else:
            recommendations.append("Data quality needs significant improvement")

    return {
        "is_valid": len(issues) == 0,
        "quality_score": round(quality_score, 2),
        "issues": issues,
        "recommendations": recommendations,
        "total_records": len(data),
        "assessment_timestamp": datetime.now().isoformat(),
    }


def _is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return bool(result.scheme and result.netloc)
    except Exception:
        return False


def _is_valid_sha256(hash_str: str) -> bool:
    """Check if string is a valid SHA256 hash."""
    return bool(re.match(r"^[a-f0-9]{64}$", hash_str.lower()))
