"""
Enhanced data validator with comprehensive error handling and reporting.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json

from ..data_io import log


# Type: ignore the error below - it's a mypy bug with field(default_factory=dict)
# Using a workaround function instead
def _make_dict() -> Dict[str, Any]:
    """Factory function for empty dict."""
    return {}


@dataclass
class ValidationError:
    """Represents a single validation error."""

    field: str
    message: str
    value: Any
    error_type: str
    severity: str = "error"  # error, warning, info
    context: Dict[str, Any] = field(default_factory=_make_dict)  # type: ignore[operator]


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(
        self,
        field: str,
        message: str,
        value: Any = None,
        error_type: str = "validation",
    ) -> None:
        """Add an error to the result."""
        error = ValidationError(field, message, value, error_type, "error")
        self.errors.append(error)
        self.is_valid = False

    def add_warning(
        self,
        field: str,
        message: str,
        value: Any = None,
        error_type: str = "validation",
    ) -> None:
        """Add a warning to the result."""
        warning = ValidationError(field, message, value, error_type, "warning")
        self.warnings.append(warning)

    def add_info(
        self, field: str, message: str, value: Any = None, error_type: str = "info"
    ) -> None:
        """Add an info message to the result."""
        info = ValidationError(field, message, value, error_type, "info")
        self.info.append(info)

    @property
    def total_issues(self) -> int:
        """Total number of issues (errors + warnings)."""
        return len(self.errors) + len(self.warnings)

    @property
    def error_count(self) -> int:
        """Number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Number of warnings."""
        return len(self.warnings)

    def get_errors_by_type(self, error_type: str) -> List[ValidationError]:
        """Get errors filtered by type."""
        return [error for error in self.errors if error.error_type == error_type]

    def get_warnings_by_type(self, error_type: str) -> List[ValidationError]:
        """Get warnings filtered by type."""
        return [
            warning for warning in self.warnings if warning.error_type == error_type
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "total_issues": self.total_issues,
            "errors": [
                {
                    "field": error.field,
                    "message": error.message,
                    "value": str(error.value) if error.value is not None else None,
                    "error_type": error.error_type,
                    "severity": error.severity,
                    "context": error.context,
                }
                for error in self.errors
            ],
            "warnings": [
                {
                    "field": warning.field,
                    "message": warning.message,
                    "value": str(warning.value) if warning.value is not None else None,
                    "error_type": warning.error_type,
                    "severity": warning.severity,
                    "context": warning.context,
                }
                for warning in self.warnings
            ],
            "info": [
                {
                    "field": info.field,
                    "message": info.message,
                    "value": str(info.value) if info.value is not None else None,
                    "error_type": info.error_type,
                    "severity": info.severity,
                    "context": info.context,
                }
                for info in self.info
            ],
            "metadata": self.metadata,
        }


class DataValidator:
    """Enhanced data validator with comprehensive validation rules."""

    def __init__(self):
        self.validation_rules: Dict[str, List[Callable]] = {}
        self.custom_validators: Dict[str, Callable] = {}

    def add_validation_rule(self, field: str, validator_func: Callable) -> None:
        """Add a validation rule for a specific field."""
        if field not in self.validation_rules:
            self.validation_rules[field] = []
        self.validation_rules[field].append(validator_func)

    def add_custom_validator(self, name: str, validator_func: Callable) -> None:
        """Add a custom validator function."""
        self.custom_validators[name] = validator_func

    def validate_field(
        self, field: str, value: Any, context: Dict[str, Any] | None = None
    ) -> ValidationResult:
        """Validate a single field."""
        result = ValidationResult(is_valid=True)

        if context is None:
            context = {}

        # Apply field-specific validation rules
        if field in self.validation_rules:
            for validator in self.validation_rules[field]:
                try:
                    if not validator(value, context):
                        result.add_error(
                            field,
                            f"Validation failed for {field}",
                            value,
                            "field_validation",
                        )
                except Exception as e:
                    result.add_error(
                        field,
                        f"Validation error for {field}: {str(e)}",
                        value,
                        "validation_exception",
                    )

        # Apply common validation rules
        self._apply_common_rules(field, value, result, context)

        return result

    def validate_record(
        self, record: Dict[str, Any], schema: Dict[str, Any] | None = None
    ) -> ValidationResult:
        """Validate a complete record."""
        result = ValidationResult(is_valid=True)

        # Validate each field
        for field_name, value in record.items():
            field_result = self.validate_field(field_name, value, {"record": record})

            # Merge results
            result.errors.extend(field_result.errors)
            result.warnings.extend(field_result.warnings)
            result.info.extend(field_result.info)
            if not field_result.is_valid:
                result.is_valid = False

        # Apply record-level validation
        self._validate_record_level(record, result)

        return result

    def validate_dataset(
        self, dataset: List[Dict[str, Any]], schema: Dict[str, Any] | None = None
    ) -> ValidationResult:
        """Validate a complete dataset."""
        result = ValidationResult(is_valid=True)

        if not dataset:
            result.add_warning("dataset", "Dataset is empty", None, "empty_dataset")
            return result

        # Validate each record
        for i, record in enumerate(dataset):
            record_result = self.validate_record(record, schema)

            # Add record index to errors
            for error in record_result.errors:
                error.context["record_index"] = i
                result.errors.append(error)

            for warning in record_result.warnings:
                warning.context["record_index"] = i
                result.warnings.append(warning)

            if not record_result.is_valid:
                result.is_valid = False

        # Apply dataset-level validation
        self._validate_dataset_level(dataset, result)

        return result

    def _apply_common_rules(
        self, field: str, value: Any, result: ValidationResult, context: Dict[str, Any]
    ) -> None:
        """Apply common validation rules."""
        # Check for required fields
        if value is None or value == "":
            if field in ["source_url", "sha256", "domain"]:  # Common required fields
                result.add_error(
                    field,
                    f"Required field {field} is missing or empty",
                    value,
                    "required_field",
                )

        # Check for valid URLs
        if field == "source_url" and value:
            if not self._is_valid_url(str(value)):
                result.add_error(
                    field, f"Invalid URL format: {value}", value, "invalid_url"
                )

        # Check for valid SHA256 hashes
        if field == "sha256" and value:
            if not self._is_valid_sha256(str(value)):
                result.add_error(
                    field, f"Invalid SHA256 hash: {value}", value, "invalid_hash"
                )

        # Check for valid domains
        if field == "domain" and value:
            valid_domains = ["tax", "accounting", "reporting"]
            if value not in valid_domains:
                result.add_error(
                    field,
                    f"Invalid domain: {value}. Must be one of {valid_domains}",
                    value,
                    "invalid_domain",
                )

    def _validate_record_level(
        self, record: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Apply record-level validation rules."""
        # Check for consistent metadata
        if "source_url" in record and "sha256" in record:
            if not record["source_url"] and record["sha256"]:
                result.add_warning(
                    "metadata",
                    "SHA256 provided but no source URL",
                    None,
                    "inconsistent_metadata",
                )

        # Check for required combinations
        if "domain" in record and "source_type" in record:
            domain = record["domain"]
            source_type = record["source_type"]

            # Domain-specific validation
            if domain == "tax" and source_type not in [
                "law",
                "forskrift",
                "rates",
                "guidance",
            ]:
                result.add_warning(
                    "source_type",
                    f"Unusual source type for tax domain: {source_type}",
                    source_type,
                    "unusual_combination",
                )

    def _validate_dataset_level(
        self, dataset: List[Dict[str, Any]], result: ValidationResult
    ) -> None:
        """Apply dataset-level validation rules."""
        # Check for duplicates
        seen_hashes = set()
        duplicate_hashes = []

        for i, record in enumerate(dataset):
            if "sha256" in record and record["sha256"]:
                if record["sha256"] in seen_hashes:
                    duplicate_hashes.append(i)
                else:
                    seen_hashes.add(record["sha256"])

        if duplicate_hashes:
            result.add_warning(
                "dataset",
                f"Found {len(duplicate_hashes)} duplicate records",
                duplicate_hashes,
                "duplicates",
            )

        # Check for consistent domains
        domains = [record.get("domain") for record in dataset if record.get("domain")]
        unique_domains = set(domains)

        if len(unique_domains) > 1:
            result.add_info(
                "dataset",
                f"Dataset contains multiple domains: {list(unique_domains)}",
                list(unique_domains),
                "multi_domain",
            )

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

        return bool(re.match(r"^[a-f0-9]{64}$", hash_str.lower()))

    def generate_report(
        self, result: ValidationResult, output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""
        report = {
            "validation_summary": {
                "timestamp": datetime.now().isoformat(),
                "is_valid": result.is_valid,
                "total_issues": result.total_issues,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "info_count": len(result.info),
            },
            "issues_by_type": {},
            "issues_by_field": {},
            "detailed_results": result.to_dict(),
        }

        # Group issues by type
        for error in result.errors:
            error_type = error.error_type
            if error_type not in report["issues_by_type"]:
                report["issues_by_type"][error_type] = 0
            report["issues_by_type"][error_type] += 1

        # Group issues by field
        for error in result.errors + result.warnings:
            field = error.field
            if field not in report["issues_by_field"]:
                report["issues_by_field"][field] = 0
            report["issues_by_field"][field] += 1

        # Save to file if requested
        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                log.info(f"Validation report saved to {output_file}")
            except Exception as e:
                log.error(f"Failed to save validation report: {e}")

        return report
