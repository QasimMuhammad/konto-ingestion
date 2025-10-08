#!/usr/bin/env python3
"""
VAT rates parser for Skatteetaten.
Extracts VAT rates and their validity periods from HTML content.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime


@dataclass
class VatRate:
    """VAT rate entry."""

    kind: str
    value: str
    percentage: float
    valid_from: Optional[str]
    valid_to: Optional[str]
    description: str
    source_url: str
    sha256: str
    category: str = ""
    applies_to: List[str] | None = None
    exceptions: List[str] | None = None
    notes: str = ""
    publisher: str = "Skatteetaten"
    is_current: bool = True
    last_updated: str = ""

    def __post_init__(self):
        if self.applies_to is None:
            self.applies_to = []
        if self.exceptions is None:
            self.exceptions = []
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


def parse_mva_rates(html: str, source_url: str, sha256: str) -> List[VatRate]:
    """
    Parse MVA rates from Skatteetaten HTML content with detailed extraction.

    Args:
        html: Raw HTML content
        source_url: Source URL for metadata
        sha256: Content hash for metadata

    Returns:
        List of VatRate objects with detailed information
    """
    soup = BeautifulSoup(html, "lxml")
    rates: List[VatRate] = []

    # Look for main content area
    main_content = soup.find("main") or soup.find(
        "div", class_=re.compile(r"content|main|article")
    )
    if not main_content:
        main_content = soup

    # Extract detailed rate information from tables
    if hasattr(main_content, "find_all"):
        tables = main_content.find_all("table")
    else:
        tables = []

    for table in tables:
        if hasattr(table, "find_all"):
            rows = table.find_all("tr")
        else:
            rows = []

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                # Extract text from cells
                cols = [cell.get_text(" ", strip=True) for cell in cells]

                # Skip header rows
                if any(
                    header in cols[0].lower()
                    for header in ["type", "sats", "rate", "kategori", "beskrivelse"]
                ):
                    continue

                # Extract detailed rate information
                rate_info = extract_detailed_rate_from_row(cols, source_url, sha256)
                if rate_info:
                    rates.append(rate_info)

    # Extract additional rate information from text content
    if hasattr(main_content, "find_all"):
        rate_sections = main_content.find_all(
            ["div", "section", "p"], class_=re.compile(r"rate|sats|mva")
        )
    else:
        rate_sections = []

    for section in rate_sections:
        text = section.get_text(" ", strip=True)
        if any(
            keyword in text.lower()
            for keyword in ["%", "prosent", "sats", "merverdiavgift"]
        ):
            rate_info = extract_rate_from_detailed_text(text, source_url, sha256)
            if rate_info:
                rates.append(rate_info)

    # Extract special rate information from links and additional content
    if hasattr(main_content, "find_all"):
        rate_links = main_content.find_all("a", href=re.compile(r"satser|mva.*sats"))
    else:
        rate_links = []

    for link in rate_links:
        link_text = link.get_text(" ", strip=True)
        if any(keyword in link_text.lower() for keyword in ["sats", "rate", "mva"]):
            # Try to find associated content
            parent_section = link.find_parent(["div", "section", "p"])
            if parent_section:
                context = parent_section.get_text(" ", strip=True)
                rate_info = extract_rate_from_detailed_text(context, source_url, sha256)
                if rate_info:
                    rates.append(rate_info)

    return rates


def extract_detailed_rate_from_row(
    cols: List[str], source_url: str, sha256: str
) -> Optional[VatRate]:
    """Extract detailed rate information from table row columns."""
    if len(cols) < 2:
        return None

    # Look for percentage in any column
    percentage = None
    percentage_str = ""
    description = ""
    category = ""

    for i, col in enumerate(cols):
        # Look for percentage pattern
        match = re.search(r"(\d+[,\s]*\d*)\s*%", col)
        if match:
            percentage_str = match.group(1)
            percentage_str = percentage_str.replace(",", ".")
            try:
                percentage = float(percentage_str)
                # Get description from other columns
                if i == 0:  # Percentage in first column, description in others
                    description = " ".join(cols[1:])
                else:  # Description in first column, percentage in others
                    description = cols[0]
                break
            except ValueError:
                continue

    if percentage is None:
        return None

    # Determine category and kind from description
    category, kind = determine_detailed_category(description)

    # Extract validity dates
    valid_from, valid_to = extract_validity_dates(cols)

    # Create detailed description
    detailed_description = create_detailed_description(
        description, percentage_str, category
    )

    # Determine what this rate applies to
    applies_to = determine_detailed_applies_to(description, category)

    # Extract exceptions and special cases
    exceptions = extract_exceptions_from_description(description)

    return VatRate(
        kind=kind,
        value=f"{percentage_str}%",
        percentage=percentage,
        valid_from=valid_from,
        valid_to=valid_to,
        description=detailed_description,
        source_url=source_url,
        sha256=sha256,
        category=category,
        applies_to=applies_to,
        exceptions=exceptions,
        notes=extract_notes_from_description(description),
        publisher="Skatteetaten",
        is_current=True,
        last_updated=datetime.now().isoformat(),
    )


def extract_rate_from_detailed_text(
    text: str, source_url: str, sha256: str
) -> Optional[VatRate]:
    """Extract rate information from detailed text content."""
    # Look for percentage pattern
    match = re.search(r"(\d+[,\s]*\d*)\s*%", text)
    if not match:
        return None

    percentage_str = match.group(1).replace(",", ".")
    try:
        percentage = float(percentage_str)
    except ValueError:
        return None

    # Extract context around the percentage
    context_start = max(0, text.find(match.group(0)) - 100)
    context_end = min(len(text), text.find(match.group(0)) + 100)
    context = text[context_start:context_end]

    # Determine category and kind
    category, kind = determine_detailed_category(context)

    # Create detailed description
    description = create_detailed_description(context, percentage_str, category)

    # Determine what this rate applies to
    applies_to = determine_detailed_applies_to(context, category)

    # Extract exceptions
    exceptions = extract_exceptions_from_description(context)

    return VatRate(
        kind=kind,
        value=f"{percentage_str}%",
        percentage=percentage,
        valid_from=None,  # Extract from context if available
        valid_to=None,
        description=description,
        source_url=source_url,
        sha256=sha256,
        category=category,
        applies_to=applies_to,
        exceptions=exceptions,
        notes=extract_notes_from_description(context),
        publisher="Skatteetaten",
        is_current=True,
        last_updated=datetime.now().isoformat(),
    )


def determine_detailed_category(description: str) -> tuple[str, str]:
    """Determine detailed category and kind from description."""
    desc_lower = description.lower()

    # Food and nutrition
    if any(
        word in desc_lower
        for word in ["næringsmidler", "mat", "food", "kjøtt", "fisk", "grønnsaker"]
    ):
        return "food_products", "reduced"

    # Water and sewage services
    elif any(
        word in desc_lower
        for word in ["vann", "avløp", "water", "sewage", "drikkevann"]
    ):
        return "water_services", "reduced"

    # Transport and entertainment
    elif any(
        word in desc_lower
        for word in [
            "persontransport",
            "kinobilletter",
            "utleie",
            "transport",
            "kino",
            "idrett",
            "fornøyelse",
        ]
    ):
        return "transport_entertainment", "reduced"

    # General/standard rate
    elif any(
        word in desc_lower for word in ["alminnelig", "standard", "generell", "hoved"]
    ):
        return "general_goods_services", "standard"

    # Zero-rated items
    elif any(word in desc_lower for word in ["null", "zero", "fritatt", "unntatt"]):
        return "exempt_goods_services", "zero"

    # Default to standard
    else:
        return "general_goods_services", "standard"


def create_detailed_description(
    description: str, percentage_str: str, category: str
) -> str:
    """Create detailed description for the rate."""
    # Clean up description
    clean_desc = re.sub(r"\s+", " ", description.strip())

    # Create detailed description based on category
    if category == "food_products":
        return f"Redusert MVA-sats for næringsmidler: {percentage_str}% - gjelder matvarer, drikkevarer og andre næringsmidler"
    elif category == "water_services":
        return f"Redusert MVA-sats for vann- og avløpstjenester: {percentage_str}% - gjelder drikkevann, avløpshåndtering og vannforsyning"
    elif category == "transport_entertainment":
        return f"Redusert MVA-sats for persontransport og underholdning: {percentage_str}% - gjelder persontransport, kinobilletter, hotellrom, idrettsarrangementer"
    elif category == "general_goods_services":
        return f"Standard MVA-sats: {percentage_str}% - gjelder de fleste varer og tjenester"
    elif category == "exempt_goods_services":
        return f"Null MVA-sats: {percentage_str}% - gjelder eksport, enkelte helsetjenester og utdanningslitteratur"
    else:
        return f"MVA-sats: {percentage_str}% - {clean_desc}"


def determine_detailed_applies_to(description: str, category: str) -> List[str]:
    """Determine what this rate applies to with detailed categories."""
    # desc_lower = description.lower()  # Not currently used
    applies_to = []

    if category == "food_products":
        applies_to = [
            "Matvarer og drikkevarer",
            "Næringsmidler for menneskeforbruk",
            "Råvarer til matproduksjon",
            "Kjott, fisk, grønnsaker, frukt",
        ]
    elif category == "water_services":
        applies_to = [
            "Drikkevann og vannforsyning",
            "Avløpshåndtering",
            "Vann- og avløpstjenester",
            "Renovasjon og avfallshåndtering",
        ]
    elif category == "transport_entertainment":
        applies_to = [
            "Persontransport (buss, tog, fly)",
            "Kinobilletter og underholdning",
            "Hotellrom og overnatting",
            "Idrettsarrangementer og fornøyelsesparker",
        ]
    elif category == "general_goods_services":
        applies_to = [
            "De fleste varer og tjenester",
            "Generell omsetning",
            "Standard handel og tjenesteyting",
        ]
    elif category == "exempt_goods_services":
        applies_to = [
            "Eksport av varer og tjenester",
            "Enkelte helsetjenester",
            "Utdanningslitteratur",
            "Fritatte tjenester",
        ]
    else:
        applies_to = ["Generelle varer og tjenester"]

    return applies_to


def extract_exceptions_from_description(description: str) -> List[str]:
    """Extract exceptions and special cases from description."""
    exceptions = []
    desc_lower = description.lower()

    # Look for exception patterns
    if "unntatt" in desc_lower or "bortsett fra" in desc_lower:
        # Try to extract exception text
        exception_match = re.search(r"(?:unntatt|bortsett fra)\s+([^.]*)", desc_lower)
        if exception_match:
            exceptions.append(exception_match.group(1).strip())

    # Look for specific exception patterns
    if "alkohol" in desc_lower:
        exceptions.append("Alkoholholdige drikkevarer har høyere sats")
    if "tobakk" in desc_lower:
        exceptions.append("Tobakksvarer har høyere sats")
    if "bil" in desc_lower and "transport" in desc_lower:
        exceptions.append("Godstransport har standard sats")

    return exceptions


def extract_notes_from_description(description: str) -> str:
    """Extract additional notes from description."""
    # Look for notes in parentheses or after asterisks
    notes_match = re.search(r"[*]\s*([^.]*)", description)
    if notes_match:
        return notes_match.group(1).strip()

    # Look for additional context
    if len(description) > 100:
        return f"Detaljert beskrivelse: {description[:200]}..."

    return ""


def extract_rate_from_row(cols: List[str]) -> Optional[Dict[str, Any]]:
    """Extract rate information from table row columns."""
    if len(cols) < 2:
        return None

    # Look for percentage in any column
    percentage = None
    percentage_str = ""

    for col in cols:
        # Look for percentage pattern
        match = re.search(r"(\d+[,\s]*\d*)\s*%", col)
        if match:
            percentage_str = match.group(1)
            # Convert to float, handling both comma and dot as decimal separator
            percentage_str = percentage_str.replace(",", ".")
            try:
                percentage = float(percentage_str)
                break
            except ValueError:
                continue

    if percentage is None:
        return None

    # Determine rate kind from first column or context
    kind = determine_rate_kind(cols[0])

    # Extract validity dates if available
    valid_from, valid_to = extract_validity_dates(cols)

    # Create description
    description = f"{kind.title()} rate: {percentage_str}%"
    if valid_from:
        description += f" (from {valid_from})"

    return {
        "kind": kind,
        "value": f"{percentage_str}%",
        "percentage": percentage,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "description": description,
    }


def extract_rate_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract rate information from text content."""
    # Look for percentage pattern
    match = re.search(r"(\d+[,\s]*\d*)\s*%", text)
    if not match:
        return None

    percentage_str = match.group(1).replace(",", ".")
    try:
        percentage = float(percentage_str)
    except ValueError:
        return None

    # Determine rate kind from context
    kind = determine_rate_kind(text)

    # Extract validity dates
    valid_from, valid_to = extract_validity_dates([text])

    description = f"{kind.title()} rate: {percentage_str}%"
    if valid_from:
        description += f" (from {valid_from})"

    return {
        "kind": kind,
        "value": f"{percentage_str}%",
        "percentage": percentage,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "description": description,
    }


def determine_rate_kind(text: str) -> str:
    """Determine the kind of VAT rate from text context."""
    text_lower = text.lower()

    # Standard rate patterns
    if any(word in text_lower for word in ["standard", "ordinær", "hoved", "normal"]):
        return "standard"
    elif any(word in text_lower for word in ["lav", "reduced", "redusert", "lavere"]):
        return "lav"
    elif any(word in text_lower for word in ["null", "zero", "0%", "ingen", "fritatt"]):
        return "null"
    elif any(word in text_lower for word in ["høy", "high", "økt", "økning"]):
        return "høy"
    elif any(word in text_lower for word in ["mva", "merverdiavgift", "vat"]):
        return "mva"
    else:
        # Default to standard if no specific pattern found
        return "standard"


def extract_validity_dates(cols: List[str]) -> tuple[Optional[str], Optional[str]]:
    """Extract validity dates from columns."""
    valid_from = None
    valid_to = None

    for col in cols:
        # Look for date patterns
        date_match = re.search(r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})", col)
        if date_match:
            date_str = date_match.group(1)
            # Normalize date format
            try:
                # Try different date formats
                for fmt in ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt).date()
                        if valid_from is None:
                            valid_from = parsed_date.strftime("%Y-%m-%d")
                        else:
                            valid_to = parsed_date.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
            except ValueError:
                continue

    return valid_from, valid_to


def get_standard_rates() -> List[VatRate]:
    """Get standard Norwegian VAT rates as fallback."""
    return [
        VatRate(
            kind="standard",
            value="25%",
            percentage=25.0,
            valid_from="2024-01-01",
            valid_to=None,
            description="Standard VAT rate: 25%",
            source_url="https://www.skatteetaten.no/satser/merverdiavgift/",
            sha256="",
        ),
        VatRate(
            kind="lav",
            value="15%",
            percentage=15.0,
            valid_from="2024-01-01",
            valid_to=None,
            description="Reduced VAT rate: 15%",
            source_url="https://www.skatteetaten.no/satser/merverdiavgift/",
            sha256="",
        ),
        VatRate(
            kind="lav",
            value="12%",
            percentage=12.0,
            valid_from="2024-01-01",
            valid_to=None,
            description="Reduced VAT rate: 12%",
            source_url="https://www.skatteetaten.no/satser/merverdiavgift/",
            sha256="",
        ),
        VatRate(
            kind="null",
            value="0%",
            percentage=0.0,
            valid_from="2024-01-01",
            valid_to=None,
            description="Zero VAT rate: 0%",
            source_url="https://www.skatteetaten.no/satser/merverdiavgift/",
            sha256="",
        ),
    ]
