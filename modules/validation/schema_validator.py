"""
Enhanced schema validator with Pydantic integration and detailed error reporting.
"""

from pathlib import Path
from typing import Dict, List, Any, Type, Union
import json

from pydantic import BaseModel, ValidationError as PydanticValidationError

from .validator import DataValidator, ValidationResult
from ..data_io import log


class SchemaValidator:
    """Enhanced schema validator with Pydantic integration."""

    def __init__(self):
        self.schemas: Dict[str, Type[BaseModel]] = {}
        self.validator = DataValidator()

    def register_schema(self, name: str, schema_class: Type[BaseModel]) -> None:
        """Register a Pydantic schema for validation."""
        self.schemas[name] = schema_class
        log.info(f"Registered schema: {name}")

    def validate_with_schema(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]], schema_name: str
    ) -> ValidationResult:
        """Validate data against a registered Pydantic schema."""
        if schema_name not in self.schemas:
            result = ValidationResult(is_valid=False)
            result.add_error(
                "schema",
                f"Schema '{schema_name}' not found",
                schema_name,
                "missing_schema",
            )
            return result

        schema_class = self.schemas[schema_name]

        if isinstance(data, list):
            return self._validate_list_with_schema(data, schema_class, schema_name)
        else:
            return self._validate_record_with_schema(data, schema_class, schema_name)

    def _validate_record_with_schema(
        self, record: Dict[str, Any], schema_class: Type[BaseModel], schema_name: str
    ) -> ValidationResult:
        """Validate a single record against a Pydantic schema."""
        result = ValidationResult(is_valid=True)

        try:
            # Validate with Pydantic
            validated_record = schema_class(**record)

            # Convert back to dict for additional validation
            validated_dict = validated_record.model_dump()

            # Run additional custom validation
            custom_result = self.validator.validate_record(validated_dict)
            result.errors.extend(custom_result.errors)
            result.warnings.extend(custom_result.warnings)
            result.info.extend(custom_result.info)

            if not custom_result.is_valid:
                result.is_valid = False

            # Add success info
            result.add_info(
                "validation",
                f"Record validated successfully with schema {schema_name}",
                None,
                "schema_validation",
            )

        except PydanticValidationError as e:
            result.is_valid = False

            # Convert Pydantic errors to our format
            for error in e.errors():
                field = (
                    ".".join(str(x) for x in error["loc"])
                    if error["loc"]
                    else "unknown"
                )
                message = error["msg"]
                error_type = error["type"]

                result.add_error(
                    field,
                    f"Schema validation error: {message}",
                    None,
                    f"pydantic_{error_type}",
                )

            log.error(f"Schema validation failed for {schema_name}: {e}")

        except Exception as e:
            result.is_valid = False
            result.add_error(
                "schema",
                f"Unexpected validation error: {str(e)}",
                None,
                "validation_exception",
            )
            log.error(f"Unexpected error during schema validation: {e}")

        return result

    def _validate_list_with_schema(
        self,
        records: List[Dict[str, Any]],
        schema_class: Type[BaseModel],
        schema_name: str,
    ) -> ValidationResult:
        """Validate a list of records against a Pydantic schema."""
        result = ValidationResult(is_valid=True)

        if not records:
            result.add_warning(
                "dataset",
                "Empty dataset provided for validation",
                None,
                "empty_dataset",
            )
            return result

        # Validate each record
        for i, record in enumerate(records):
            record_result = self._validate_record_with_schema(
                record, schema_class, schema_name
            )

            # Add record index to errors
            for error in record_result.errors:
                error.context["record_index"] = i
                result.errors.append(error)

            for warning in record_result.warnings:
                warning.context["record_index"] = i
                result.warnings.append(warning)

            result.info.extend(record_result.info)

            if not record_result.is_valid:
                result.is_valid = False

        # Dataset-level validation
        self._validate_dataset_consistency(records, result, schema_name)

        return result

    def _validate_dataset_consistency(
        self, records: List[Dict[str, Any]], result: ValidationResult, schema_name: str
    ) -> None:
        """Validate dataset-level consistency."""
        # Check for duplicates based on common unique fields
        unique_fields = ["source_url", "sha256", "rule_id", "node_path"]

        for field in unique_fields:
            if field in records[0] if records else False:
                seen_values = set()
                duplicates = []

                for i, record in enumerate(records):
                    value = record.get(field)
                    if value:
                        if value in seen_values:
                            duplicates.append(i)
                        else:
                            seen_values.add(value)

                if duplicates:
                    result.add_warning(
                        field,
                        f"Found {len(duplicates)} duplicate {field} values",
                        duplicates,
                        "duplicates",
                    )

        # Check for consistent domains
        domains = [record.get("domain") for record in records if record.get("domain")]
        unique_domains = set(domains)

        if len(unique_domains) > 1:
            result.add_info(
                "domain",
                f"Dataset contains multiple domains: {list(unique_domains)}",
                list(unique_domains),
                "multi_domain",
            )

        # Check for consistent publishers
        publishers = [
            record.get("publisher") for record in records if record.get("publisher")
        ]
        unique_publishers = set(publishers)

        if len(unique_publishers) > 1:
            result.add_info(
                "publisher",
                f"Dataset contains multiple publishers: {list(unique_publishers)}",
                list(unique_publishers),
                "multi_publisher",
            )

    def validate_file(self, file_path: Path, schema_name: str) -> ValidationResult:
        """Validate a JSON file against a schema."""
        if not file_path.exists():
            result = ValidationResult(is_valid=False)
            result.add_error(
                "file", f"File not found: {file_path}", str(file_path), "file_not_found"
            )
            return result

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate the data
            result = self.validate_with_schema(data, schema_name)

            # Add file metadata
            result.metadata["file_path"] = str(file_path)
            result.metadata["file_size"] = file_path.stat().st_size
            result.metadata["schema_name"] = schema_name

            return result

        except json.JSONDecodeError as e:
            result = ValidationResult(is_valid=False)
            result.add_error(
                "file",
                f"Invalid JSON in file {file_path}: {str(e)}",
                str(file_path),
                "json_decode_error",
            )
            return result

        except Exception as e:
            result = ValidationResult(is_valid=False)
            result.add_error(
                "file",
                f"Error reading file {file_path}: {str(e)}",
                str(file_path),
                "file_read_error",
            )
            return result

    def validate_directory(
        self, directory: Path, schema_mapping: Dict[str, str]
    ) -> Dict[str, ValidationResult]:
        """Validate all JSON files in a directory against their respective schemas."""
        results: dict[str, ValidationResult] = {}

        if not directory.exists():
            log.error(f"Directory not found: {directory}")
            return results

        # Find all JSON files
        json_files = list(directory.glob("*.json"))

        if not json_files:
            log.warning(f"No JSON files found in {directory}")
            return results

        log.info(f"Validating {len(json_files)} JSON files in {directory}")

        for json_file in json_files:
            file_name = json_file.name

            # Determine schema for this file
            schema_name = None
            for pattern, schema in schema_mapping.items():
                if pattern in file_name.lower():
                    schema_name = schema
                    break

            if not schema_name:
                log.warning(f"No schema mapping found for {file_name}")
                continue

            # Validate the file
            result = self.validate_file(json_file, schema_name)
            results[file_name] = result

            # Log result
            if result.is_valid:
                log.info(
                    f"✓ {file_name}: Valid ({result.error_count} errors, {result.warning_count} warnings)"
                )
            else:
                log.error(
                    f"✗ {file_name}: Invalid ({result.error_count} errors, {result.warning_count} warnings)"
                )

        return results

    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a summary of registered schemas."""
        return {
            "registered_schemas": list(self.schemas.keys()),
            "schema_count": len(self.schemas),
            "schemas": {
                name: {
                    "fields": list(schema.model_fields.keys()),
                    "field_count": len(schema.model_fields),
                }
                for name, schema in self.schemas.items()
            },
        }
