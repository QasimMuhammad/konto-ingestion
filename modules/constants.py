#!/usr/bin/env python3
"""
Constants and enumerations for konto-ingestion.
Eliminates magic strings and provides type safety.
"""

from enum import Enum


class Domains(str, Enum):
    """Data domains."""

    TAX = "tax"
    ACCOUNTING = "accounting"
    REPORTING = "reporting"


class SourceTypes(str, Enum):
    """Source types."""

    LAW = "law"
    FORSKRIFT = "forskrift"
    SPEC = "spec"
    GUIDANCE = "guidance"
    RATES = "rates"


class Publishers(str, Enum):
    """Data publishers."""

    LOVDATA = "Lovdata"
    SKATTEETATEN = "Skatteetaten"
    ALTINN = "Altinn"


class Priorities(str, Enum):
    """Priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Complexity(str, Enum):
    """Complexity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CrawlFrequencies(str, Enum):
    """Crawl frequencies."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ONCHANGE = "onchange"
    DAILY = "daily"


class AmeldingCategories(str, Enum):
    """A-meldingen rule categories."""

    FORM_GUIDANCE = "form_guidance"
    SUBMISSION_DEADLINES = "submission_deadlines"
    EMPLOYER_OBLIGATIONS = "employer_obligations"
    GENERAL_GUIDANCE = "general_guidance"
    SALARY_REPORTING = "salary_reporting"


class VatRateKinds(str, Enum):
    """VAT rate kinds."""

    STANDARD = "standard"
    REDUCED = "reduced"
    ZERO = "zero"
    EXEMPT = "exempt"


class VatRateCategories(str, Enum):
    """VAT rate categories."""

    GENERAL_GOODS = "general_goods"
    FOOD_PRODUCTS = "food_products"
    WATER_SERVICES = "water_services"
    TRANSPORT_ENTERTAINMENT = "transport_entertainment"
    MEDICAL_SERVICES = "medical_services"


class DataTypes(str, Enum):
    """Data types for technical specifications."""

    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    COMPLEX = "complex"


class Cardinalities(str, Enum):
    """Cardinality specifications."""

    ONE = "1..1"
    ZERO_OR_ONE = "0..1"
    ONE_OR_MORE = "1..*"
    ZERO_OR_MORE = "0..*"


# File extensions
class FileExtensions(str, Enum):
    """Common file extensions."""

    HTML = ".html"
    PDF = ".pdf"
    JSON = ".json"
    JSONL = ".jsonl"
    CSV = ".csv"
    XML = ".xml"


# HTTP status codes
class HTTPStatus(int, Enum):
    """HTTP status codes."""

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


# Processing limits
class ProcessingLimits:
    """Processing limits and thresholds."""

    MIN_TEXT_LENGTH = 50
    MAX_TEXT_LENGTH = 10000
    MAX_RETRIES = 3
    HTTP_TIMEOUT = 30
    BATCH_SIZE = 100
    MAX_MEMORY_MB = 1000


# Error messages
class ErrorMessages:
    """Standard error messages."""

    SOURCE_NOT_FOUND = "Source '{source_id}' not found in sources.csv"
    PARSING_FAILED = "Failed to parse {content_type} content"
    VALIDATION_FAILED = "Validation failed for {entity_type}"
    NETWORK_ERROR = "Network error: {error}"
    FILE_NOT_FOUND = "File not found: {file_path}"
    INVALID_CONFIG = "Invalid configuration: {setting}"


# Success messages
class SuccessMessages:
    """Standard success messages."""

    PROCESSING_COMPLETE = "Processing completed successfully"
    VALIDATION_PASSED = "All validations passed"
    DATA_SAVED = "Data saved successfully"
    SCRIPT_COMPLETE = "Script completed successfully"
