#!/usr/bin/env python3
"""
A-meldingen (A-melding) parser.
Extracts detailed A-melding rules and guidance from Skatteetaten and Altinn HTML content.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime


@dataclass
class AmeldingRule:
    """A-melding rule entry with detailed information."""

    rule_id: str
    title: str
    description: str
    category: str
    applies_to: List[str]
    requirements: List[str]
    examples: List[str]
    source_url: str
    sha256: str
    domain: str = "reporting"
    source_type: str = "guidance"
    publisher: str = "Skatteetaten"
    jurisdiction: str = "NO"
    is_current: bool = True
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    priority: str = "medium"
    complexity: str = "low"
    last_updated: str = datetime.now().isoformat()
    technical_details: List[str] | None = None
    validation_rules: List[str] | None = None
    field_mappings: Dict[str, str] | None = None
    business_rules: List[str] | None = None

    def __post_init__(self):
        if self.technical_details is None:
            self.technical_details = []
        if self.validation_rules is None:
            self.validation_rules = []
        if self.field_mappings is None:
            self.field_mappings = {}
        if self.business_rules is None:
            self.business_rules = []


def parse_amelding_overview(
    html: str, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """
    Parse A-meldingen overview page from Skatteetaten with detailed extraction.

    Args:
        html: Raw HTML content
        source_url: Source URL for metadata
        sha256: Content hash for metadata

    Returns:
        List of AmeldingRule objects with detailed information
    """
    soup = BeautifulSoup(html, "lxml")
    rules: List[AmeldingRule] = []

    # Look for main content area
    main_content = soup.find("main") or soup.find(
        "div", class_=re.compile(r"content|main|article")
    )
    if not main_content:
        main_content = soup

    # Extract detailed rules from various content structures
    rules.extend(extract_rules_from_headings(main_content, source_url, sha256))
    rules.extend(extract_rules_from_lists(main_content, source_url, sha256))
    rules.extend(extract_rules_from_tables(main_content, source_url, sha256))
    rules.extend(extract_rules_from_forms(main_content, source_url, sha256))
    rules.extend(extract_rules_from_links(main_content, source_url, sha256))

    return rules


def parse_amelding_forms(html: str, source_url: str, sha256: str) -> List[AmeldingRule]:
    """
    Parse A-meldingen forms page from Altinn with detailed extraction.

    Args:
        html: Raw HTML content
        source_url: Source URL for metadata
        sha256: Content hash for metadata

    Returns:
        List of AmeldingRule objects with detailed information
    """
    soup = BeautifulSoup(html, "lxml")
    rules: List[AmeldingRule] = []

    # Look for main content area
    main_content = soup.find("main") or soup.find(
        "div", class_=re.compile(r"content|main|article")
    )
    if not main_content:
        main_content = soup

    # Extract form-specific rules
    rules.extend(extract_form_field_rules(main_content, source_url, sha256))
    rules.extend(extract_validation_rules(main_content, source_url, sha256))
    rules.extend(extract_submission_rules(main_content, source_url, sha256))
    rules.extend(extract_business_logic_rules(main_content, source_url, sha256))

    return rules


def extract_rules_from_headings(
    main_content, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """Extract rules from headings and their content."""
    rules: List[AmeldingRule] = []
    headings = main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    for heading in headings:
        heading_text = heading.get_text(" ", strip=True)

        # Skip navigation and non-rule headings
        if any(
            skip in heading_text.lower()
            for skip in ["navigasjon", "meny", "innhold", "overskrift", "cookie"]
        ):
            continue

        # Look for content after heading
        content_elements = []
        current = heading.find_next_sibling()

        while current and current.name not in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            if current.name in ["p", "ul", "ol", "div", "table"]:
                content_elements.append(current)
            current = current.find_next_sibling()

        # Extract detailed text content
        content_text = " ".join(
            [elem.get_text(" ", strip=True) for elem in content_elements]
        )

        if content_text and len(content_text) > 20:  # Minimum content length
            # Extract detailed rule information
            rule_id = f"amelding_heading_{len(rules) + 1:03d}"
            category = extract_detailed_category(heading_text, content_text)
            applies_to = extract_detailed_applies_to(content_text, category)
            requirements = extract_detailed_requirements(content_text, category)
            examples = extract_detailed_examples(content_text, category)
            technical_details = extract_technical_details(content_text, category)
            validation_rules = extract_validation_rules_from_text(
                content_text, category
            )
            field_mappings = extract_field_mappings(content_text, category)
            business_rules = extract_business_rules(content_text, category)

            rules.append(
                AmeldingRule(
                    rule_id=rule_id,
                    title=heading_text,
                    description=content_text,
                    category=category,
                    applies_to=applies_to,
                    requirements=requirements,
                    examples=examples,
                    source_url=source_url,
                    sha256=sha256,
                    technical_details=technical_details,
                    validation_rules=validation_rules,
                    field_mappings=field_mappings,
                    business_rules=business_rules,
                    priority=determine_priority(category, content_text),
                    complexity=determine_complexity(content_text, technical_details),
                )
            )

    return rules


def extract_rules_from_lists(
    main_content, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """Extract rules from lists and bullet points."""
    rules: List[AmeldingRule] = []
    lists = main_content.find_all(["ul", "ol"])

    for list_elem in lists:
        # Check if this is a rule-related list
        parent_text = ""
        parent = list_elem.find_parent(["div", "section", "article"])
        if parent:
            parent_text = parent.get_text(" ", strip=True)

        if not any(
            keyword in parent_text.lower()
            for keyword in ["a-melding", "rapportering", "skjema", "frist", "krav"]
        ):
            continue

        items = list_elem.find_all("li")
        for i, item in enumerate(items):
            item_text = item.get_text(" ", strip=True)
            if len(item_text) > 10:  # Minimum content length
                rule_id = f"amelding_list_{len(rules) + 1:03d}"
                category = extract_detailed_category(item_text, parent_text)
                applies_to = extract_detailed_applies_to(item_text, category)
                requirements = extract_detailed_requirements(item_text, category)
                technical_details = extract_technical_details(item_text, category)

                rules.append(
                    AmeldingRule(
                        rule_id=rule_id,
                        title=f"Regel {i + 1}: {item_text[:50]}...",
                        description=item_text,
                        category=category,
                        applies_to=applies_to,
                        requirements=requirements,
                        examples=[],
                        source_url=source_url,
                        sha256=sha256,
                        technical_details=technical_details,
                        priority=determine_priority(category, item_text),
                        complexity="low",
                    )
                )

    return rules


def extract_rules_from_tables(
    main_content, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """Extract rules from tables with structured data."""
    rules: List[AmeldingRule] = []
    tables = main_content.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:  # Need at least header and one data row
            continue

        # Extract headers
        headers = []
        header_row = rows[0]
        for cell in header_row.find_all(["th", "td"]):
            headers.append(cell.get_text(" ", strip=True))

        # Process data rows
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.get_text(" ", strip=True)

                # Create rule from table data
                if any(
                    keyword in str(row_data).lower()
                    for keyword in ["a-melding", "rapportering", "skjema"]
                ):
                    rule_id = f"amelding_table_{len(rules) + 1:03d}"
                    description = " | ".join([f"{k}: {v}" for k, v in row_data.items()])

                    rules.append(
                        AmeldingRule(
                            rule_id=rule_id,
                            title=f"Tabellregel: {list(row_data.values())[0][:30]}...",
                            description=description,
                            category="data_structure",
                            applies_to=["A-melding data"],
                            requirements=extract_detailed_requirements(
                                description, "data_structure"
                            ),
                            examples=[],
                            source_url=source_url,
                            sha256=sha256,
                            priority="medium",
                            complexity="medium",
                        )
                    )

    return rules


def extract_rules_from_forms(
    main_content, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """Extract rules from form elements and input fields."""
    rules: List[AmeldingRule] = []
    forms = main_content.find_all("form")

    for form in forms:
        form_text = form.get_text(" ", strip=True)
        if not any(
            keyword in form_text.lower()
            for keyword in ["a-melding", "rapportering", "skjema"]
        ):
            continue

        # Extract form fields and their requirements
        inputs = form.find_all(["input", "select", "textarea"])
        for input_elem in inputs:
            input_name = input_elem.get("name", "")
            input_type = input_elem.get("type", "text")
            required = input_elem.get("required") is not None

            if input_name:
                rule_id = f"amelding_form_{len(rules) + 1:03d}"

                rules.append(
                    AmeldingRule(
                        rule_id=rule_id,
                        title=f"Skjemafelt: {input_name}",
                        description=f"Felt '{input_name}' av type '{input_type}' {'(påkrevd)' if required else '(valgfri)'}",
                        category="form_guidance",
                        applies_to=["A-melding skjema"],
                        requirements=[
                            f"Felt {input_name} må fylles ut"
                            if required
                            else f"Felt {input_name} er valgfri"
                        ],
                        examples=[],
                        source_url=source_url,
                        sha256=sha256,
                        priority="high" if required else "medium",
                        complexity="low",
                    )
                )

    return rules


def extract_rules_from_links(
    main_content, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """Extract rules from relevant links and their context."""
    rules: List[AmeldingRule] = []
    links = main_content.find_all("a", href=True)

    for link in links:
        link_text = link.get_text(" ", strip=True)

        if any(
            keyword in link_text.lower()
            for keyword in [
                "a-melding",
                "rapportering",
                "skjema",
                "veiledning",
                "regel",
            ]
        ):
            # Get context around the link
            parent = link.find_parent(["div", "section", "p"])
            context = parent.get_text(" ", strip=True) if parent else link_text

            rule_id = f"amelding_link_{len(rules) + 1:03d}"
            category = extract_detailed_category(link_text, context)

            rules.append(
                AmeldingRule(
                    rule_id=rule_id,
                    title=f"Lenkeregel: {link_text}",
                    description=context,
                    category=category,
                    applies_to=extract_detailed_applies_to(context, category),
                    requirements=extract_detailed_requirements(context, category),
                    examples=[],
                    source_url=source_url,
                    sha256=sha256,
                    priority="medium",
                    complexity="low",
                )
            )

    return rules


def extract_form_field_rules(
    main_content, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """Extract detailed form field rules."""
    rules: List[AmeldingRule] = []

    # Look for form fields with detailed specifications
    inputs = main_content.find_all(["input", "select", "textarea"])

    for input_elem in inputs:
        input_name = input_elem.get("name", "")
        input_type = input_elem.get("type", "text")
        required = input_elem.get("required") is not None
        pattern = input_elem.get("pattern", "")
        maxlength = input_elem.get("maxlength", "")
        minlength = input_elem.get("minlength", "")

        if input_name:
            rule_id = f"amelding_field_{len(rules) + 1:03d}"

            # Extract field description from labels or nearby text
            label = input_elem.find_previous("label")
            description = (
                label.get_text(" ", strip=True) if label else f"Felt {input_name}"
            )

            # Create detailed requirements
            requirements = []
            if required:
                requirements.append(f"Felt {input_name} er påkrevd")
            if pattern:
                requirements.append(f"Felt {input_name} må matche mønster: {pattern}")
            if maxlength:
                requirements.append(
                    f"Felt {input_name} kan maksimalt ha {maxlength} tegn"
                )
            if minlength:
                requirements.append(f"Felt {input_name} må ha minst {minlength} tegn")

                rules.append(
                    AmeldingRule(
                        rule_id=rule_id,
                        title=f"Skjemafelt: {input_name}",
                        description=description,
                        category="form_guidance",
                        applies_to=["A-melding skjema", f"Felt {input_name}"],
                        requirements=requirements,
                        examples=[],
                        source_url=source_url,
                        sha256=sha256,
                        technical_details=[
                            f"Type: {input_type}",
                            f"Navn: {input_name}",
                        ],
                        validation_rules=requirements,
                        priority="high" if required else "medium",
                        complexity="low",
                    )
                )

    return rules


def extract_validation_rules(
    main_content, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """Extract validation rules and constraints."""
    rules: List[AmeldingRule] = []

    # Look for validation-related content
    validation_elements = main_content.find_all(
        string=re.compile(r"validering|valider|gyldig|ugyldig|feil|error")
    )

    for element in validation_elements:
        parent = element.parent
        if parent:
            context = parent.get_text(" ", strip=True)
            if len(context) > 20:
                rule_id = f"amelding_validation_{len(rules) + 1:03d}"

                rules.append(
                    AmeldingRule(
                        rule_id=rule_id,
                        title=f"Valideringsregel: {context[:50]}...",
                        description=context,
                        category="form_guidance",
                        applies_to=["A-melding data"],
                        requirements=extract_detailed_requirements(
                            context, "form_guidance"
                        ),
                        examples=[],
                        source_url=source_url,
                        sha256=sha256,
                        priority="high",
                        complexity="medium",
                    )
                )

    return rules


def extract_submission_rules(
    main_content, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """Extract submission rules and deadlines."""
    rules: List[AmeldingRule] = []

    # Look for deadline and submission content
    deadline_elements = main_content.find_all(
        string=re.compile(r"frist|deadline|innlever|submission|måned|år")
    )

    for element in deadline_elements:
        parent = element.parent
        if parent:
            context = parent.get_text(" ", strip=True)
            if len(context) > 20:
                rule_id = f"amelding_submission_{len(rules) + 1:03d}"

                rules.append(
                    AmeldingRule(
                        rule_id=rule_id,
                        title=f"Innleveringsregel: {context[:50]}...",
                        description=context,
                        category="submission_deadlines",
                        applies_to=["A-melding innlevering"],
                        requirements=extract_detailed_requirements(
                            context, "submission_deadlines"
                        ),
                        examples=[],
                        source_url=source_url,
                        sha256=sha256,
                        priority="high",
                        complexity="low",
                    )
                )

    return rules


def extract_business_logic_rules(
    main_content, source_url: str, sha256: str
) -> List[AmeldingRule]:
    """Extract business logic rules and calculations."""
    rules: List[AmeldingRule] = []

    # Look for calculation and business logic content
    calc_elements = main_content.find_all(
        string=re.compile(r"beregn|kalkuler|formel|regel|logikk")
    )

    for element in calc_elements:
        parent = element.parent
        if parent:
            context = parent.get_text(" ", strip=True)
            if len(context) > 20:
                rule_id = f"amelding_business_{len(rules) + 1:03d}"

                rules.append(
                    AmeldingRule(
                        rule_id=rule_id,
                        title=f"Forretningsregel: {context[:50]}...",
                        description=context,
                        category="business_logic",
                        applies_to=["A-melding beregninger"],
                        requirements=extract_detailed_requirements(
                            context, "business_logic"
                        ),
                        examples=[],
                        source_url=source_url,
                        sha256=sha256,
                        priority="high",
                        complexity="high",
                    )
                )

    return rules


def extract_detailed_category(heading_text: str, content_text: str) -> str:
    """Extract detailed category from heading and content."""
    text = f"{heading_text} {content_text}".lower()

    if any(word in text for word in ["skjema", "form", "felt", "input"]):
        return "form_guidance"
    elif any(word in text for word in ["validering", "valider", "gyldig", "feil"]):
        return "form_guidance"
    elif any(word in text for word in ["frist", "deadline", "innlever", "submission"]):
        return "submission_deadlines"
    elif any(word in text for word in ["skjemafelt", "felt", "input", "field"]):
        return "form_guidance"
    elif any(word in text for word in ["beregn", "kalkuler", "formel", "regel"]):
        return "salary_reporting"
    elif any(word in text for word in ["data", "struktur", "format", "xml"]):
        return "form_guidance"
    elif any(word in text for word in ["arbeidsgiver", "lønn", "skatt", "trekk"]):
        return "employer_obligations"
    elif any(word in text for word in ["ansatt", "person", "navn", "fødselsnummer"]):
        return "salary_reporting"
    elif any(word in text for word in ["trekk", "skatt", "avgift"]):
        return "tax_deductions"
    else:
        return "general_guidance"


def extract_detailed_applies_to(content_text: str, category: str) -> List[str]:
    """Extract detailed applies_to information."""
    applies_to = []

    if category == "form_field":
        applies_to = ["A-melding skjema", "Skjemafelter", "Datainnsamling"]
    elif category == "validation":
        applies_to = ["A-melding data", "Datavalidering", "Kvalitetskontroll"]
    elif category == "submission":
        applies_to = ["A-melding innlevering", "Rapportering", "Frister"]
    elif category == "business_logic":
        applies_to = ["A-melding beregninger", "Forretningsregler", "Logikk"]
    elif category == "data_structure":
        applies_to = ["A-melding data", "Datastruktur", "Format"]
    elif category == "payroll":
        applies_to = ["Lønnsdata", "Arbeidsgiver", "Skattetrekk"]
    elif category == "employee_data":
        applies_to = ["Ansattdata", "Personopplysninger", "Identifikasjon"]
    else:
        applies_to = ["A-melding generelt"]

    return applies_to


def extract_detailed_requirements(content_text: str, category: str) -> List[str]:
    """Extract detailed requirements from content."""
    requirements = []

    # Look for requirement patterns
    req_patterns = [
        r"må\s+([^.]*)",
        r"skal\s+([^.]*)",
        r"påkrevd\s+([^.]*)",
        r"obligatorisk\s+([^.]*)",
        r"krav\s+([^.]*)",
    ]

    for pattern in req_patterns:
        matches = re.findall(pattern, content_text.lower())
        for match in matches:
            requirements.append(match.strip())

    # Add category-specific requirements
    if category == "form_field":
        requirements.append("Alle påkrevde felter må fylles ut")
    elif category == "validation":
        requirements.append("Data må valideres før innlevering")
    elif category == "submission":
        requirements.append("Innlevering må skje innen frist")

    return requirements


def extract_detailed_examples(content_text: str, category: str) -> List[str]:
    """Extract detailed examples from content."""
    examples = []

    # Look for example patterns
    example_patterns = [
        r"eksempel\s*:?\s*([^.]*)",
        r"for eksempel\s*:?\s*([^.]*)",
        r"f\.eks\.\s*([^.]*)",
    ]

    for pattern in example_patterns:
        matches = re.findall(pattern, content_text.lower())
        for match in matches:
            examples.append(match.strip())

    return examples


def extract_technical_details(content_text: str, category: str) -> List[str]:
    """Extract technical details from content."""
    technical_details = []

    # Look for technical patterns
    tech_patterns = [
        r"format\s*:?\s*([^.]*)",
        r"type\s*:?\s*([^.]*)",
        r"lengde\s*:?\s*([^.]*)",
        r"maksimalt\s*([^.]*)",
        r"minimalt\s*([^.]*)",
    ]

    for pattern in tech_patterns:
        matches = re.findall(pattern, content_text.lower())
        for match in matches:
            technical_details.append(match.strip())

    return technical_details


def extract_validation_rules_from_text(content_text: str, category: str) -> List[str]:
    """Extract validation rules from text."""
    validation_rules = []

    # Look for validation patterns
    val_patterns = [
        r"valider\s+([^.]*)",
        r"kontroller\s+([^.]*)",
        r"sjekk\s+([^.]*)",
        r"gyldig\s+([^.]*)",
    ]

    for pattern in val_patterns:
        matches = re.findall(pattern, content_text.lower())
        for match in matches:
            validation_rules.append(match.strip())

    return validation_rules


def extract_field_mappings(content_text: str, category: str) -> Dict[str, str]:
    """Extract field mappings from content."""
    field_mappings = {}

    # Look for field mapping patterns
    mapping_patterns = [
        r"(\w+)\s*→\s*(\w+)",
        r"(\w+)\s*til\s*(\w+)",
        r"(\w+)\s*mapper\s*til\s*(\w+)",
    ]

    for pattern in mapping_patterns:
        matches = re.findall(pattern, content_text.lower())
        for match in matches:
            field_mappings[match[0]] = match[1]

    return field_mappings


def extract_business_rules(content_text: str, category: str) -> List[str]:
    """Extract business rules from content."""
    business_rules = []

    # Look for business rule patterns
    rule_patterns = [
        r"hvis\s+([^.]*)",
        r"dersom\s+([^.]*)",
        r"når\s+([^.]*)",
        r"regel\s*:?\s*([^.]*)",
    ]

    for pattern in rule_patterns:
        matches = re.findall(pattern, content_text.lower())
        for match in matches:
            business_rules.append(match.strip())

    return business_rules


def determine_priority(category: str, content_text: str) -> str:
    """Determine priority based on category and content."""
    if category in ["validation", "submission", "form_field"]:
        return "high"
    elif category in ["business_logic", "data_structure"]:
        return "medium"
    else:
        return "low"


def determine_complexity(content_text: str, technical_details: List[str]) -> str:
    """Determine complexity based on content and technical details."""
    if len(technical_details) > 3 or any(
        word in content_text.lower() for word in ["beregn", "kalkuler", "formel"]
    ):
        return "high"
    elif len(technical_details) > 1 or any(
        word in content_text.lower() for word in ["valider", "kontroller"]
    ):
        return "medium"
    else:
        return "low"


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text.strip())

    # Remove HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")

    return text
