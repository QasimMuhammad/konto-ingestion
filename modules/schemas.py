"""
Consolidated schema definitions for all data types.
Pydantic V2 models for Bronze, Silver, and Gold layers.
"""

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LawSection(BaseModel):
    """Law section schema for legal documents."""

    law_id: str = Field(..., description="Unique identifier for the law")
    section_id: str = Field(..., description="Section identifier (e.g., PARAGRAF_1-1)")
    section_label: str = Field(
        ..., description="Human-readable section label (e.g., § 1-1)"
    )
    path: str = Field(
        ..., description="Full path to section (e.g., Kapittel 1 PARAGRAF_1-1)"
    )
    heading: str = Field(..., description="Section heading")
    text_plain: str = Field(..., description="Cleaned plain text content")
    source_url: str = Field(..., description="Source URL")
    sha256: str = Field(..., description="Content hash")
    domain: str = Field(..., description="Domain (tax, accounting, reporting)")
    source_type: str = Field(..., description="Source type (law, forskrift, spec)")
    publisher: str = Field(..., description="Publisher (Lovdata, Skatteetaten, etc.)")
    version: str = Field(..., description="Version identifier")
    jurisdiction: str = Field(..., description="Jurisdiction (NO, EU, etc.)")
    effective_from: Optional[str] = Field(None, description="Effective from date")
    effective_to: Optional[str] = Field(None, description="Effective to date")
    law_title: str = Field(..., description="Full law title")
    chapter: str = Field(..., description="Chapter name")
    chapter_no: str = Field(..., description="Chapter number")
    section_no: Optional[str] = Field(None, description="Section number")
    subsection_no: Optional[str] = Field(None, description="Subsection number")
    paragraph_no: Optional[str] = Field(None, description="Paragraph number")
    text_length: Optional[int] = Field(None, description="Text length in characters")
    word_count: Optional[int] = Field(None, description="Word count")
    has_citations: Optional[bool] = Field(
        None, description="Whether section contains citations"
    )
    has_amendments: Optional[bool] = Field(
        None, description="Whether section has amendments"
    )
    is_current: Optional[bool] = Field(
        None, description="Whether section is currently in force"
    )
    last_updated: Optional[str] = Field(None, description="Last updated timestamp")
    token_count: Optional[int] = Field(None, description="Token count for LLM")
    crawl_freq: Optional[str] = Field(None, description="Crawl frequency")

    model_config = ConfigDict(json_encoders={})


class VatRate(BaseModel):
    """VAT (MVA) rate schema."""

    rate_id: str
    rate_label: str
    rate_value: float
    description: str
    effective_from: str
    effective_to: Optional[str] = None
    source_url: str
    sha256: str
    domain: str
    source_type: str
    publisher: str
    jurisdiction: str = "NO"
    last_updated: Optional[str] = None
    token_count: Optional[int] = None
    crawl_freq: Optional[str] = None

    model_config = ConfigDict(json_encoders={})


class SpecNode(BaseModel):
    """SAF-T specification node schema."""

    node_id: str
    node_path: str
    node_label: str
    node_level: int
    parent_id: Optional[str] = None
    data_type: Optional[str] = None
    description: str
    cardinality: Optional[str] = None
    example_value: Optional[str] = None
    validation_rules: List[str] = Field(default_factory=list)
    technical_details: List[str] = Field(default_factory=list)
    source_url: str
    sha256: str
    domain: str = "accounting"
    source_type: str = "spec"
    publisher: str
    version: str = "1.3"
    jurisdiction: str = "NO"
    last_updated: Optional[str] = None
    token_count: Optional[int] = None
    crawl_freq: Optional[str] = None

    model_config = ConfigDict(json_encoders={})


class AmeldingRule(BaseModel):
    """A-melding (employee reporting) rule schema."""

    rule_id: str
    category: str
    subcategory: str
    field_id: str
    field_label: str
    description: str
    data_type: Optional[str] = None
    cardinality: Optional[str] = None
    validation_rules: List[str] = Field(default_factory=list)
    example_value: Optional[str] = None
    source_url: str
    sha256: str
    domain: str = "reporting"
    source_type: str = "spec"
    publisher: str
    version: str
    jurisdiction: str = "NO"
    last_updated: Optional[str] = None
    token_count: Optional[int] = None
    crawl_freq: Optional[str] = None

    model_config = ConfigDict(json_encoders={})


class QualityReport(BaseModel):
    """Quality assessment report schema."""

    overall_score: float
    completeness_score: float
    consistency_score: float
    accuracy_score: float
    timeliness_score: float
    total_records: int
    valid_records: int
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    assessment_date: str

    model_config = ConfigDict(json_encoders={})


class SilverMetadata(BaseModel):
    """Metadata for Silver layer dataset."""

    dataset_name: str
    version: str
    created_at: str
    total_files: int
    total_records: int
    domains: List[str]
    source_types: List[str]
    publishers: List[str]
    quality_score: float

    model_config = ConfigDict(json_encoders={})


class ChartOfAccountsEntry(BaseModel):
    """Chart of Accounts entry schema (Norwegian Standard NS 4102)."""

    account_id: str = Field(
        ..., pattern=r"^\d{4}$", description="4-digit account number"
    )
    account_label: str = Field(..., description="Account name/label")
    account_class: Literal["1", "2", "3", "4", "5", "6", "7", "8"] = Field(
        ..., description="Account class (1-8)"
    )
    account_class_label: Literal[
        "Eiendeler",
        "Egenkapital og gjeld",
        "Inntekter",
        "Kostnader",
        "Finansposter",
    ] = Field(..., description="Class label")
    account_group: Optional[str] = Field(None, description="Account group within class")
    account_group_label: Optional[str] = Field(None, description="Group label/name")
    description: str = Field(..., description="Detailed account description")
    account_type: Literal["asset", "liability", "equity", "income", "expense"] = Field(
        ..., description="Account type"
    )
    normal_balance: Literal["debit", "credit"] = Field(
        ..., description="Normal balance direction"
    )
    is_standard: bool = Field(
        True, description="Whether this is a standard NS 4102 account"
    )
    is_active: bool = Field(True, description="Whether account is active")
    examples: List[str] = Field(default_factory=list, description="Usage examples")
    related_vat_codes: List[
        Literal["HIGH", "MEDIUM", "LOW", "EXEMPT", "REVERSE_CHARGE"]
    ] = Field(default_factory=list, description="Related VAT codes")
    source_standard: str = Field(default="NS 4102", description="Source standard")
    jurisdiction: str = Field(default="NO", description="Jurisdiction")
    last_updated: Optional[str] = Field(None, description="Last updated timestamp")

    model_config = ConfigDict(json_encoders={})


class RuleCondition(BaseModel):
    """Strongly typed condition for business rules."""

    field: str = Field(..., description="Field name to evaluate")
    operator: Literal[
        "equals",
        "not_equals",
        "contains",
        "not_contains",
        "in",
        "not_in",
        "greater_than",
        "less_than",
        "greater_equal",
        "less_equal",
    ] = Field(..., description="Comparison operator")
    value: Union[str, int, float, bool, List[str]] = Field(
        ..., description="Value to compare against"
    )

    model_config = ConfigDict(json_encoders={})


class RuleAction(BaseModel):
    """Strongly typed action for business rules."""

    type: Literal[
        "set_account",
        "set_vat_code",
        "set_vat_rate",
        "set_vat_account",
        "set_posting_type",
        "set_asset_category",
    ] = Field(..., description="Action type")
    value: Union[str, int, float] = Field(..., description="Action value")

    model_config = ConfigDict(json_encoders={})


class ExampleInput(BaseModel):
    """Example input for rule testing."""

    amount: Union[int, float]
    category: str | None = None
    country: str | None = None
    description: str | None = None
    context: str | None = None
    supplier_vat_registered: bool | None = None

    model_config = ConfigDict(extra="allow", json_encoders={})


class ExampleOutput(BaseModel):
    """Example output for rule testing."""

    account: str
    vat_code: Literal["HIGH", "MEDIUM", "LOW", "EXEMPT", "REVERSE_CHARGE"] | None = None
    vat_rate: Union[int, float] | None = None
    vat_account: str | None = None
    posting_type: str | None = None

    model_config = ConfigDict(extra="allow", json_encoders={})


class RuleExample(BaseModel):
    """Typed example scenario for business rules."""

    description: str
    input: ExampleInput
    output: ExampleOutput

    model_config = ConfigDict(json_encoders={})


class BusinessRule(BaseModel):
    """Business rule schema with strong typing for deterministic posting proposals."""

    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="Rule description")
    category: Literal[
        "expense", "income", "vat_calculation", "posting_logic", "transfer"
    ] = Field(..., description="Rule category")
    domain: Literal["tax", "accounting", "reporting", "payroll"] = Field(
        ..., description="Domain"
    )
    priority: int = Field(
        default=100, description="Rule priority (lower = higher priority)"
    )
    is_active: bool = Field(True, description="Whether rule is active")
    conditions: List[RuleCondition] = Field(..., description="Typed rule conditions")
    actions: List[RuleAction] = Field(..., description="Typed actions to take")
    source_ids: List[str] = Field(
        ...,
        description="References to source documents (law sections, VAT rates, etc.)",
    )
    citations: List[str] = Field(
        default_factory=list, description="Human-readable citations"
    )
    examples: List[RuleExample] = Field(
        default_factory=list, description="Typed example scenarios"
    )
    valid_from: Optional[str] = Field(None, description="Valid from date")
    valid_to: Optional[str] = Field(None, description="Valid to date")
    jurisdiction: str = Field(default="NO", description="Jurisdiction")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    last_updated: Optional[str] = Field(None, description="Last updated timestamp")

    @field_validator("source_ids")
    @classmethod
    def validate_source_ids_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("source_ids cannot be empty")
        return v

    model_config = ConfigDict(json_encoders={})


class GoldMessage(BaseModel):
    """Single message in OpenAI chat format for training data."""

    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1, description="Message content")

    model_config = ConfigDict(json_encoders={})


class GoldMetadata(BaseModel):
    """Metadata for Gold training samples."""

    domain: Literal["tax", "accounting", "reporting", "payroll"]
    task: Literal["glossary_define", "posting_proposal", "conversation", "vat_question"]
    source_ids: list[str] = Field(..., min_length=1, description="Source document IDs")
    locale: Literal["nb-NO", "en-US"] = "nb-NO"
    split: Literal["train", "val"] = "train"
    rule_ids: list[str] | None = None
    conversation_type: str | None = None
    turns: int | None = None
    created_at: str | None = None

    model_config = ConfigDict(json_encoders={})


class GoldTrainingSample(BaseModel):
    """Complete Gold layer training sample in JSONL format."""

    messages: list[GoldMessage] = Field(..., min_length=2, description="Chat messages")
    metadata: GoldMetadata

    @field_validator("messages")
    @classmethod
    def validate_message_flow(cls, v: list[GoldMessage]) -> list[GoldMessage]:
        """Ensure messages follow system -> user -> assistant pattern."""
        if len(v) < 2:
            raise ValueError("Must have at least 2 messages")
        if v[0].role != "system":
            raise ValueError("First message must be system")
        return v

    model_config = ConfigDict(json_encoders={})


__all__ = [
    "LawSection",
    "VatRate",
    "SpecNode",
    "AmeldingRule",
    "QualityReport",
    "SilverMetadata",
    "ChartOfAccountsEntry",
    "RuleCondition",
    "RuleAction",
    "ExampleInput",
    "ExampleOutput",
    "RuleExample",
    "BusinessRule",
    "GoldMessage",
    "GoldMetadata",
    "GoldTrainingSample",
]
