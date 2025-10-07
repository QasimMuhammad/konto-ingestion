#!/usr/bin/env python3
"""
SAF-T (Standard Audit File for Tax) parser.
Extracts detailed SAF-T specification nodes and technical requirements from HTML content.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime


@dataclass
class SpecNode:
    """SAF-T specification node with detailed information."""

    spec: str
    version: str
    node_path: str
    cardinality: str
    description: str
    source_url: str
    sha256: str
    domain: str = "tax"
    source_type: str = "specification"
    publisher: str = "Skatteetaten"
    jurisdiction: str = "NO"
    is_current: bool = True
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    priority: str = "medium"
    complexity: str = "medium"
    last_updated: str = datetime.now().isoformat()
    data_type: str = ""
    format: str = ""
    validation_rules: List[str] | None = None
    business_rules: List[str] | None = None
    examples: List[str] | None = None
    dependencies: List[str] | None = None
    technical_details: List[str] | None = None

    def __post_init__(self):
        if self.validation_rules is None:
            self.validation_rules = []
        if self.business_rules is None:
            self.business_rules = []
        if self.examples is None:
            self.examples = []
        if self.dependencies is None:
            self.dependencies = []
        if self.technical_details is None:
            self.technical_details = []


def parse_saft_page(
    html: str, version: str, source_url: str, sha256: str
) -> List[SpecNode]:
    """
    Parse SAF-T specification page with detailed extraction.

    Args:
        html: Raw HTML content
        version: SAF-T version
        source_url: Source URL for metadata
        sha256: Content hash for metadata

    Returns:
        List of SpecNode objects with detailed information
    """
    soup = BeautifulSoup(html, "lxml")
    nodes: List[SpecNode] = []

    # Look for main content area
    main_content = soup.find("main") or soup.find(
        "div", class_=re.compile(r"content|main|article")
    )
    if not main_content:
        main_content = soup

    # Extract nodes from various content structures
    nodes.extend(extract_nodes_from_tables(main_content, version, source_url, sha256))
    nodes.extend(extract_nodes_from_lists(main_content, version, source_url, sha256))
    nodes.extend(extract_nodes_from_headings(main_content, version, source_url, sha256))
    nodes.extend(
        extract_nodes_from_code_blocks(main_content, version, source_url, sha256)
    )
    nodes.extend(
        extract_nodes_from_documentation(main_content, version, source_url, sha256)
    )

    return nodes


def extract_nodes_from_tables(
    main_content, version: str, source_url: str, sha256: str
) -> List[SpecNode]:
    """Extract nodes from tables with structured data."""
    nodes: List[SpecNode] = []
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

                # Create node from table data
                if any(
                    keyword in str(row_data).lower()
                    for keyword in ["saft", "node", "element", "field"]
                ):
                    node = create_detailed_node_from_table_data(
                        row_data, version, source_url, sha256
                    )
                    if node:
                        nodes.append(node)

    return nodes


def extract_nodes_from_lists(
    main_content, version: str, source_url: str, sha256: str
) -> List[SpecNode]:
    """Extract nodes from lists and bullet points."""
    nodes: List[SpecNode] = []
    lists = main_content.find_all(["ul", "ol"])

    for list_elem in lists:
        # Check if this is a SAF-T related list
        parent_text = ""
        parent = list_elem.find_parent(["div", "section", "article"])
        if parent:
            parent_text = parent.get_text(" ", strip=True)

        if not any(
            keyword in parent_text.lower()
            for keyword in ["saft", "node", "element", "field", "specification"]
        ):
            continue

        items = list_elem.find_all("li")
        for i, item in enumerate(items):
            item_text = item.get_text(" ", strip=True)
            if len(item_text) > 10:  # Minimum content length
                node = create_detailed_node_from_list_item(
                    item_text, version, source_url, sha256
                )
                if node:
                    nodes.append(node)

    return nodes


def extract_nodes_from_headings(
    main_content, version: str, source_url: str, sha256: str
) -> List[SpecNode]:
    """Extract nodes from headings and their content."""
    nodes: List[SpecNode] = []
    headings = main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    for heading in headings:
        heading_text = heading.get_text(" ", strip=True)

        # Skip navigation and non-SAF-T headings
        if any(
            skip in heading_text.lower()
            for skip in ["navigasjon", "meny", "innhold", "overskrift", "cookie"]
        ):
            continue

        # Look for content after heading
        content_elements = []
        current = heading.find_next_sibling()

        while current and current.name not in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            if current.name in ["p", "ul", "ol", "div", "table", "pre"]:
                content_elements.append(current)
            current = current.find_next_sibling()

        # Extract detailed text content
        content_text = " ".join(
            [elem.get_text(" ", strip=True) for elem in content_elements]
        )

        if content_text and len(content_text) > 20:  # Minimum content length
            node = create_detailed_node_from_heading(
                heading_text, content_text, version, source_url, sha256
            )
            if node:
                nodes.append(node)

    return nodes


def extract_nodes_from_code_blocks(
    main_content, version: str, source_url: str, sha256: str
) -> List[SpecNode]:
    """Extract nodes from code blocks and technical content."""
    nodes: List[SpecNode] = []
    code_blocks = main_content.find_all(["pre", "code"])

    for code_block in code_blocks:
        code_text = code_block.get_text(" ", strip=True)

        # Look for XML/SAF-T patterns
        if any(
            pattern in code_text.lower()
            for pattern in ["<", "xml", "saft", "node", "element"]
        ):
            # Extract node information from code
            node = create_detailed_node_from_code(
                code_text, version, source_url, sha256
            )
            if node:
                nodes.append(node)

    return nodes


def extract_nodes_from_documentation(
    main_content, version: str, source_url: str, sha256: str
) -> List[SpecNode]:
    """Extract nodes from documentation sections."""
    nodes: List[SpecNode] = []

    # Look for documentation sections
    doc_sections = main_content.find_all(
        ["div", "section"], class_=re.compile(r"doc|spec|content")
    )

    for section in doc_sections:
        section_text = section.get_text(" ", strip=True)

        if any(
            keyword in section_text.lower()
            for keyword in ["saft", "node", "element", "field", "specification"]
        ):
            # Extract node information from documentation
            node = create_detailed_node_from_documentation(
                section_text, version, source_url, sha256
            )
            if node:
                nodes.append(node)

    return nodes


def create_detailed_node_from_table_data(
    row_data: Dict[str, str], version: str, source_url: str, sha256: str
) -> Optional[SpecNode]:
    """Create detailed node from table data."""
    # Look for node path in various columns
    node_path = ""
    for key, value in row_data.items():
        if any(
            keyword in key.lower() for keyword in ["path", "node", "element", "field"]
        ):
            node_path = value
            break

    if not node_path:
        return None

    # Extract other information
    description = ""
    cardinality = ""
    data_type = ""

    for key, value in row_data.items():
        if any(
            keyword in key.lower() for keyword in ["description", "beskrivelse", "desc"]
        ):
            description = value
        elif any(
            keyword in key.lower()
            for keyword in ["cardinality", "kardinalitet", "occurs"]
        ):
            cardinality = value
        elif any(keyword in key.lower() for keyword in ["type", "datatype", "format"]):
            data_type = value

    # Create detailed node
    return SpecNode(
        spec="SAF-T",
        version=version,
        node_path=clean_node_path(node_path),
        cardinality=clean_cardinality(cardinality),
        description=description or f"SAF-T node: {node_path}",
        source_url=source_url,
        sha256=sha256,
        data_type=data_type or "string",
        format=determine_format(data_type or "string"),
        validation_rules=extract_validation_rules_from_description(description),
        business_rules=extract_business_rules_from_description(description),
        examples=extract_examples_from_description(description),
        dependencies=extract_dependencies_from_description(description),
        technical_details=extract_technical_details_from_description(description),
        priority=determine_priority_from_path(node_path),
        complexity=determine_complexity_from_description(description),
        publisher="Skatteetaten",
        is_current=True,
        last_updated=datetime.now().isoformat(),
    )


def create_detailed_node_from_list_item(
    item_text: str, version: str, source_url: str, sha256: str
) -> Optional[SpecNode]:
    """Create detailed node from list item."""
    # Look for node path pattern
    node_path_match = re.search(r"([a-zA-Z_][a-zA-Z0-9_.]*)", item_text)
    if not node_path_match:
        return None

    node_path = node_path_match.group(1)

    return SpecNode(
        spec="SAF-T",
        version=version,
        node_path=clean_node_path(node_path),
        cardinality="1",  # Default cardinality
        description=item_text,
        source_url=source_url,
        sha256=sha256,
        data_type=determine_data_type_from_text(item_text),
        format=determine_format_from_text(item_text),
        validation_rules=extract_validation_rules_from_description(item_text),
        business_rules=extract_business_rules_from_description(item_text),
        examples=extract_examples_from_description(item_text),
        dependencies=extract_dependencies_from_description(item_text),
        technical_details=extract_technical_details_from_description(item_text),
        priority=determine_priority_from_path(node_path),
        complexity=determine_complexity_from_description(item_text),
        publisher="Skatteetaten",
        is_current=True,
        last_updated=datetime.now().isoformat(),
    )


def create_detailed_node_from_heading(
    heading_text: str, content_text: str, version: str, source_url: str, sha256: str
) -> Optional[SpecNode]:
    """Create detailed node from heading and content."""
    # Look for node path in heading
    node_path_match = re.search(r"([a-zA-Z_][a-zA-Z0-9_.]*)", heading_text)
    if not node_path_match:
        return None

    node_path = node_path_match.group(1)

    return SpecNode(
        spec="SAF-T",
        version=version,
        node_path=clean_node_path(node_path),
        cardinality="1",  # Default cardinality
        description=f"{heading_text}: {content_text}",
        source_url=source_url,
        sha256=sha256,
        data_type=determine_data_type_from_text(content_text),
        format=determine_format_from_text(content_text),
        validation_rules=extract_validation_rules_from_description(content_text),
        business_rules=extract_business_rules_from_description(content_text),
        examples=extract_examples_from_description(content_text),
        dependencies=extract_dependencies_from_description(content_text),
        technical_details=extract_technical_details_from_description(content_text),
        priority=determine_priority_from_path(node_path),
        complexity=determine_complexity_from_description(content_text),
        publisher="Skatteetaten",
        is_current=True,
        last_updated=datetime.now().isoformat(),
    )


def create_detailed_node_from_code(
    code_text: str, version: str, source_url: str, sha256: str
) -> Optional[SpecNode]:
    """Create detailed node from code content."""
    # Look for XML element patterns
    element_match = re.search(r"<([a-zA-Z_][a-zA-Z0-9_.]*)", code_text)
    if not element_match:
        return None

    node_path = element_match.group(1)

    return SpecNode(
        spec="SAF-T",
        version=version,
        node_path=clean_node_path(node_path),
        cardinality="1",  # Default cardinality
        description=f"XML element: {node_path}",
        source_url=source_url,
        sha256=sha256,
        data_type="string",  # Default for XML elements
        format="XML",
        validation_rules=extract_validation_rules_from_description(code_text),
        business_rules=extract_business_rules_from_description(code_text),
        examples=extract_examples_from_description(code_text),
        dependencies=extract_dependencies_from_description(code_text),
        technical_details=extract_technical_details_from_description(code_text),
        priority=determine_priority_from_path(node_path),
        complexity=determine_complexity_from_description(code_text),
        publisher="Skatteetaten",
        is_current=True,
        last_updated=datetime.now().isoformat(),
    )


def create_detailed_node_from_documentation(
    doc_text: str, version: str, source_url: str, sha256: str
) -> Optional[SpecNode]:
    """Create detailed node from documentation content."""
    # Look for node path patterns
    node_path_match = re.search(r"([a-zA-Z_][a-zA-Z0-9_.]*)", doc_text)
    if not node_path_match:
        return None

    node_path = node_path_match.group(1)

    return SpecNode(
        spec="SAF-T",
        version=version,
        node_path=clean_node_path(node_path),
        cardinality="1",  # Default cardinality
        description=doc_text,
        source_url=source_url,
        sha256=sha256,
        data_type=determine_data_type_from_text(doc_text),
        format=determine_format_from_text(doc_text),
        validation_rules=extract_validation_rules_from_description(doc_text),
        business_rules=extract_business_rules_from_description(doc_text),
        examples=extract_examples_from_description(doc_text),
        dependencies=extract_dependencies_from_description(doc_text),
        technical_details=extract_technical_details_from_description(doc_text),
        priority=determine_priority_from_path(node_path),
        complexity=determine_complexity_from_description(doc_text),
        publisher="Skatteetaten",
        is_current=True,
        last_updated=datetime.now().isoformat(),
    )


def clean_node_path(path: str) -> str:
    """Clean and normalize node path."""
    # Remove extra whitespace
    path = re.sub(r"\s+", "", path.strip())

    # Remove common prefixes
    path = re.sub(r"^saft\.", "", path)
    path = re.sub(r"^auditfile\.", "", path)

    return path


def clean_cardinality(cardinality: str) -> str:
    """Clean and normalize cardinality."""
    if not cardinality:
        return "1"

    cardinality = cardinality.strip().lower()

    # Map common cardinality patterns
    if cardinality in ["0..1", "0-1", "optional", "valgfri"]:
        return "0..1"
    elif cardinality in ["1..1", "1", "required", "påkrevd"]:
        return "1"
    elif cardinality in ["1..*", "1+", "one or more", "en eller flere"]:
        return "1..*"
    elif cardinality in ["0..*", "0+", "zero or more", "null eller flere"]:
        return "0..*"

    return cardinality


def clean_description(description: str) -> str:
    """Clean and normalize description."""
    # Remove extra whitespace
    description = re.sub(r"\s+", " ", description.strip())

    # Remove HTML entities
    description = description.replace("&nbsp;", " ")
    description = description.replace("&amp;", "&")
    description = description.replace("&lt;", "<")
    description = description.replace("&gt;", ">")

    return description


def determine_data_type_from_text(text: str) -> str:
    """Determine data type from text content."""
    text_lower = text.lower()

    if any(word in text_lower for word in ["string", "text", "tekst"]):
        return "string"
    elif any(word in text_lower for word in ["integer", "int", "number", "tall"]):
        return "integer"
    elif any(word in text_lower for word in ["decimal", "float", "double", "desimal"]):
        return "decimal"
    elif any(word in text_lower for word in ["date", "dato", "time", "tid"]):
        return "date"
    elif any(word in text_lower for word in ["boolean", "bool", "true", "false"]):
        return "boolean"
    else:
        return "string"  # Default


def determine_format_from_text(text: str) -> str:
    """Determine format from text content."""
    text_lower = text.lower()

    if any(word in text_lower for word in ["xml", "xhtml"]):
        return "XML"
    elif any(word in text_lower for word in ["json", "javascript"]):
        return "JSON"
    elif any(word in text_lower for word in ["csv", "comma"]):
        return "CSV"
    elif any(word in text_lower for word in ["iso", "standard"]):
        return "ISO"
    else:
        return "XML"  # Default for SAF-T


def determine_format(data_type: str) -> str:
    """Determine format from data type."""
    if data_type in ["date", "datetime"]:
        return "ISO 8601"
    elif data_type in ["decimal", "float"]:
        return "Decimal"
    elif data_type in ["integer"]:
        return "Integer"
    else:
        return "String"


def extract_validation_rules_from_description(description: str) -> List[str]:
    """Extract validation rules from description."""
    validation_rules = []

    # Look for validation patterns
    val_patterns = [
        r"må\s+([^.]*)",
        r"skal\s+([^.]*)",
        r"påkrevd\s+([^.]*)",
        r"obligatorisk\s+([^.]*)",
        r"valider\s+([^.]*)",
        r"kontroller\s+([^.]*)",
    ]

    for pattern in val_patterns:
        matches = re.findall(pattern, description.lower())
        for match in matches:
            validation_rules.append(match.strip())

    return validation_rules


def extract_business_rules_from_description(description: str) -> List[str]:
    """Extract business rules from description."""
    business_rules = []

    # Look for business rule patterns
    rule_patterns = [
        r"hvis\s+([^.]*)",
        r"dersom\s+([^.]*)",
        r"når\s+([^.]*)",
        r"regel\s*:?\s*([^.]*)",
        r"krav\s*:?\s*([^.]*)",
    ]

    for pattern in rule_patterns:
        matches = re.findall(pattern, description.lower())
        for match in matches:
            business_rules.append(match.strip())

    return business_rules


def extract_examples_from_description(description: str) -> List[str]:
    """Extract examples from description."""
    examples = []

    # Look for example patterns
    example_patterns = [
        r"eksempel\s*:?\s*([^.]*)",
        r"for eksempel\s*:?\s*([^.]*)",
        r"f\.eks\.\s*([^.]*)",
    ]

    for pattern in example_patterns:
        matches = re.findall(pattern, description.lower())
        for match in matches:
            examples.append(match.strip())

    return examples


def extract_dependencies_from_description(description: str) -> List[str]:
    """Extract dependencies from description."""
    dependencies = []

    # Look for dependency patterns
    dep_patterns = [
        r"avhenger\s+av\s+([^.]*)",
        r"krever\s+([^.]*)",
        r"må\s+ha\s+([^.]*)",
        r"forutsetter\s+([^.]*)",
    ]

    for pattern in dep_patterns:
        matches = re.findall(pattern, description.lower())
        for match in matches:
            dependencies.append(match.strip())

    return dependencies


def extract_technical_details_from_description(description: str) -> List[str]:
    """Extract technical details from description."""
    technical_details = []

    # Look for technical patterns
    tech_patterns = [
        r"format\s*:?\s*([^.]*)",
        r"type\s*:?\s*([^.]*)",
        r"lengde\s*:?\s*([^.]*)",
        r"maksimalt\s*([^.]*)",
        r"minimalt\s*([^.]*)",
        r"standard\s*:?\s*([^.]*)",
    ]

    for pattern in tech_patterns:
        matches = re.findall(pattern, description.lower())
        for match in matches:
            technical_details.append(match.strip())

    return technical_details


def determine_priority_from_path(node_path: str) -> str:
    """Determine priority based on node path."""
    if any(
        keyword in node_path.lower() for keyword in ["header", "hoved", "main", "root"]
    ):
        return "high"
    elif any(
        keyword in node_path.lower() for keyword in ["required", "påkrevd", "mandatory"]
    ):
        return "high"
    elif any(
        keyword in node_path.lower() for keyword in ["optional", "valgfri", "optional"]
    ):
        return "low"
    else:
        return "medium"


def determine_complexity_from_description(description: str) -> str:
    """Determine complexity based on description."""
    if any(
        word in description.lower()
        for word in ["beregn", "kalkuler", "formel", "regel", "logikk"]
    ):
        return "high"
    elif any(
        word in description.lower() for word in ["valider", "kontroller", "sjekk"]
    ):
        return "medium"
    else:
        return "low"


def parse_saft_documentation(
    html: str, version: str, source_url: str, sha256: str
) -> List[SpecNode]:
    """
    Parse SAF-T documentation with detailed extraction.

    Args:
        html: Raw HTML content
        version: SAF-T version
        source_url: Source URL for metadata
        sha256: Content hash for metadata

    Returns:
        List of SpecNode objects with detailed information
    """
    soup = BeautifulSoup(html, "lxml")
    nodes: List[SpecNode] = []

    # Look for main content area
    main_content = soup.find("main") or soup.find(
        "div", class_=re.compile(r"content|main|article")
    )
    if not main_content:
        main_content = soup

    # Extract nodes from headings
    if hasattr(main_content, "find_all"):
        headings = main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    else:
        headings = []

    for heading in headings:
        heading_text = heading.get_text(" ", strip=True)

        # Skip navigation and non-SAF-T headings
        if any(
            skip in heading_text.lower()
            for skip in ["navigasjon", "meny", "innhold", "overskrift", "cookie"]
        ):
            continue

        # Look for content after heading
        content_elements = []
        current = heading.find_next_sibling()

        while current and current.name not in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            if current.name in ["p", "ul", "ol", "div", "table", "pre"]:
                content_elements.append(current)
            current = current.find_next_sibling()

        # Extract detailed text content
        content_text = " ".join(
            [elem.get_text(" ", strip=True) for elem in content_elements]
        )

        if content_text and len(content_text) > 20:  # Minimum content length
            node = create_detailed_node_from_heading(
                heading_text, content_text, version, source_url, sha256
            )
            if node:
                nodes.append(node)

    return nodes
