"""
Lovdata HTML parser for Norwegian legal documents.
Extracts sections, headings, and text content from Lovdata.no HTML pages.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from bs4 import BeautifulSoup, Tag

from ..cleaners.normalize_text import normalize_text


@dataclass
class Section:
    """Represents a legal section with metadata."""

    law_id: str
    section_id: str  # e.g., "§ 8-1"
    path: str  # e.g., "Kapittel 8 § 8-1"
    heading: str
    text_plain: str
    source_url: str
    sha256: str


def parse_lovdata_html(
    html: str, law_id: str, source_url: str, sha256: str
) -> List[Section]:
    """
    Parse Lovdata HTML content into structured sections.

    Args:
        html: Raw HTML content from Lovdata.no
        law_id: Identifier for the law (e.g., "mva_law_1999")
        source_url: Original URL of the document
        sha256: SHA256 hash of the HTML content

    Returns:
        List of Section objects with parsed content
    """
    soup = BeautifulSoup(html, "lxml")
    sections: List[Section] = []

    # Find all potential section elements
    # Lovdata typically uses various structures, so we'll try multiple selectors
    section_selectors = [
        "div.paragraf",
        "div.paragraf-innhold",
        "section",
        "div[class*='paragraf']",
        "div[class*='section']",
        "div[class*='kapittel']",
    ]

    found_sections = []
    for selector in section_selectors:
        elements = soup.select(selector)
        if elements:
            found_sections.extend(elements)
            break

    # If no specific sections found, look for headings and their content
    if not found_sections:
        found_sections = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    for element in found_sections:
        section = _extract_section_from_element(element, law_id, source_url, sha256)
        if section:
            sections.append(section)

    # If still no sections found, try to extract from the main content
    if not sections:
        sections = _extract_sections_from_main_content(soup, law_id, source_url, sha256)

    return sections


def _extract_section_from_element(
    element: Tag, law_id: str, source_url: str, sha256: str
) -> Optional[Section]:
    """Extract section data from a single HTML element."""
    try:
        # Try to find section ID from various attributes
        section_id = _extract_section_id(element)
        if not section_id:
            return None

        # Extract heading
        heading = _extract_heading(element)

        # Extract text content
        text_content = _extract_text_content(element)
        if not text_content or len(text_content.strip()) < 10:
            return None

        # Normalize text
        text_plain = normalize_text(text_content)

        # Create path (chapter + section)
        path = _create_section_path(element, heading, section_id)

        return Section(
            law_id=law_id,
            section_id=section_id,
            path=path,
            heading=heading,
            text_plain=text_plain,
            source_url=source_url,
            sha256=sha256,
        )

    except Exception as e:
        print(f"Error extracting section from element: {e}")
        return None


def _extract_section_id(element: Tag) -> Optional[str]:
    """Extract section ID from element attributes or content."""
    # Try ID attribute first
    if element.get("id"):
        return element.get("id")

    # Look for section markers in text content
    text = element.get_text()

    # Pattern for Norwegian legal sections: § 8-1, § 9-2, etc.
    section_pattern = r"§\s*(\d+-\d+)"
    match = re.search(section_pattern, text)
    if match:
        return f"§ {match.group(1)}"

    # Pattern for simple numbers: 8-1, 9-2, etc.
    number_pattern = r"(\d+-\d+)"
    match = re.search(number_pattern, text)
    if match:
        return f"§ {match.group(1)}"

    return None


def _extract_heading(element: Tag) -> str:
    """Extract heading text from element."""
    # Look for heading tags within the element
    heading_tags = element.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    if heading_tags:
        return heading_tags[0].get_text(" ", strip=True)

    # If no heading tags, use first line of text
    text = element.get_text(" ", strip=True)
    first_line = text.split("\n")[0].strip()
    return first_line[:100] if first_line else ""


def _extract_text_content(element: Tag) -> str:
    """Extract clean text content from element."""
    # Remove script and style elements
    for script in element(["script", "style"]):
        script.decompose()

    # Get text content
    text = element.get_text(" ", strip=True)

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _create_section_path(element: Tag, heading: str, section_id: str) -> str:
    """Create a human-readable path for the section."""
    # Try to find chapter information
    chapter_info = _find_chapter_info(element)

    if chapter_info:
        return f"{chapter_info} {section_id}"
    elif heading:
        return heading
    else:
        return section_id


def _find_chapter_info(element: Tag) -> Optional[str]:
    """Find chapter information from element or its parents."""
    # Look for chapter markers in parent elements
    current = element.parent
    while current:
        text = current.get_text()
        chapter_match = re.search(r"(Kapittel|Kapitel)\s*(\d+)", text, re.IGNORECASE)
        if chapter_match:
            return f"Kapittel {chapter_match.group(2)}"
        current = current.parent

    return None


def _extract_sections_from_main_content(
    soup: BeautifulSoup, law_id: str, source_url: str, sha256: str
) -> List[Section]:
    """Fallback method to extract sections from main content when no specific structure found."""
    sections = []

    # Look for all text that contains section markers
    text = soup.get_text()

    # Split by section markers and create sections
    section_pattern = r"(§\s*\d+-\d+[^§]*)"
    matches = re.findall(section_pattern, text, re.DOTALL)

    for i, match in enumerate(matches):
        lines = match.strip().split("\n")
        if len(lines) < 2:
            continue

        # First line should contain the section ID
        first_line = lines[0].strip()
        section_id_match = re.search(r"§\s*(\d+-\d+)", first_line)
        if not section_id_match:
            continue

        section_id = f"§ {section_id_match.group(1)}"
        heading = first_line
        text_content = "\n".join(lines[1:]).strip()

        if len(text_content) < 10:
            continue

        text_plain = normalize_text(text_content)

        sections.append(
            Section(
                law_id=law_id,
                section_id=section_id,
                path=heading,
                heading=heading,
                text_plain=text_plain,
                source_url=source_url,
                sha256=sha256,
            )
        )

    return sections
