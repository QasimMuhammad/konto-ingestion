"""
Improved text processing utilities for Silver layer data.
Handles HTML cleaning, text normalization, and metadata extraction with better parsing.
"""

import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any
from bs4 import BeautifulSoup


def clean_legal_text(text: str) -> str:
    """
    Clean legal text by removing navigation elements and unwanted content.

    Args:
        text: Raw legal text content

    Returns:
        Cleaned legal text
    """
    if not text:
        return ""

    # Remove navigation elements and links
    text = re.sub(r"🔗\s*Del paragraf", "", text)
    text = re.sub(r"🔗\s*.*", "", text)  # Remove any other link symbols
    text = re.sub(r"Se også.*", "", text)  # Remove "See also" references
    text = re.sub(r"Gå til.*", "", text)  # Remove "Go to" references

    # Remove common Lovdata navigation elements
    text = re.sub(r"\[Til toppen\]", "", text)
    text = re.sub(r"\[Tilbake\]", "", text)
    text = re.sub(r"\[Neste\]", "", text)
    text = re.sub(r"\[Forrige\]", "", text)

    # Clean up extra whitespace
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def extract_section_html(html_content: str, section_id: str) -> str:
    """
    Extract only the relevant section HTML, not the entire webpage.

    Args:
        html_content: Full HTML content
        section_id: ID of the section to extract

    Returns:
        Cleaned HTML containing only the section content
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Try to find the specific section
    section_element = None

    # Look for the section by ID
    if section_id:
        section_element = soup.find(id=section_id)

    # If not found by ID, look for paragraph elements
    if not section_element:
        section_element = soup.find("div", class_="paragraf")

    # If still not found, look for the main content area
    if not section_element:
        section_element = soup.find("div", class_="document-content")

    # If still not found, look for the main content
    if not section_element:
        section_element = soup.find("main")

    # If still not found, use the body but clean it
    if not section_element:
        section_element = soup.find("body")

    if section_element:
        # Remove navigation and unwanted elements
        for element in section_element.find_all(["nav", "header", "footer", "aside"]):
            element.decompose()

        # Remove script and style elements
        for element in section_element.find_all(["script", "style"]):
            element.decompose()

        # Remove navigation links
        for element in section_element.find_all("a", href=True):
            if "del-paragraf" in element.get("href", "").lower():
                element.decompose()

        return str(section_element)

    # Fallback: return cleaned body content
    body = soup.find("body")
    if body:
        # Remove unwanted elements
        for element in body.find_all(["script", "style", "nav", "header", "footer"]):
            element.decompose()
        return str(body)

    return ""


def normalize_text(text: str) -> str:
    """
    Normalize text by stripping HTML/JS and cleaning whitespace.

    Args:
        text: Raw text content (may contain HTML)

    Returns:
        Clean, normalized text
    """
    if not text:
        return ""

    # Parse HTML and extract text
    soup = BeautifulSoup(text, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text content
    text_content = soup.get_text()

    # Clean legal text
    text_content = clean_legal_text(text_content)

    # Normalize whitespace
    text_content = re.sub(r"\s+", " ", text_content)  # Collapse multiple whitespace
    text_content = text_content.strip()

    return text_content


def compute_stable_hash(text: str) -> str:
    """
    Compute SHA256 hash on stable canonicalization.

    Args:
        text: Text to hash

    Returns:
        SHA256 hash as hex string
    """
    if not text:
        return ""

    # Canonicalize: lowercase, trimmed, collapsed spaces, normalized unicode
    canonical = text.lower().strip()
    canonical = re.sub(r"\s+", " ", canonical)  # Collapse spaces
    canonical = canonical.encode("utf-8").decode("unicode_escape")  # Normalize unicode

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def extract_legal_metadata(
    html_content: str, metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract legal metadata from HTML content.

    Args:
        html_content: Raw HTML content
        metadata: Existing metadata dictionary

    Returns:
        Dictionary with extracted legal metadata
    """
    soup = BeautifulSoup(html_content, "html.parser")

    legal_metadata = {}

    # Extract law title
    title_selectors = [
        "h1.title",
        "h1",
        ".document-title",
        ".law-title",
        "title",
        ".main-title",
        ".page-title",
    ]

    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem and title_elem.get_text().strip():
            legal_metadata["law_title"] = title_elem.get_text().strip()
            break

    # Extract chapter information - look for actual chapter, not concatenated content
    chapter_elem = soup.select_one(".chapter, .kapittel, h2")
    if chapter_elem:
        chapter_text = chapter_elem.get_text().strip()
        if "kapittel" in chapter_text.lower() or "chapter" in chapter_text.lower():
            legal_metadata["chapter"] = chapter_text

    # Check for repealed status
    repealed_indicators = ["opphevet", "repealed", "ikrafttredelse", "endret"]
    page_text = soup.get_text().lower()
    legal_metadata["repealed"] = any(
        indicator in page_text for indicator in repealed_indicators
    )

    # Extract amendment dates from footnotes or headers
    amendment_patterns = [
        r"endret ved (?:lov|forskrift)[^0-9]*(\d{1,2}\s+\w+\s+\d{4})",
        r"ikrafttredelse[^0-9]*(\d{1,2}\s+\w+\s+\d{4})",
        r"(\d{1,2}\s+\w+\s+\d{4})[^0-9]*(?:endret|ikrafttredelse)",
    ]

    amendments = []
    for pattern in amendment_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        amendments.extend(matches)

    if amendments:
        legal_metadata["amended_dates"] = list(set(amendments))  # Remove duplicates

    return legal_metadata


def enhance_section_metadata(
    section, metadata: Dict[str, Any], html_content: str
) -> Dict[str, Any]:
    """
    Enhance section with comprehensive metadata using improved parsing.

    Args:
        section: Section object from parser
        metadata: Source metadata dictionary
        html_content: Raw HTML content

    Returns:
        Enhanced section metadata dictionary
    """
    # Clean the text content
    cleaned_text = clean_legal_text(section.text_plain)
    normalized_text = normalize_text(cleaned_text)

    # Compute stable hash
    stable_hash = compute_stable_hash(normalized_text)

    # Extract only the relevant section HTML
    section_html = extract_section_html(html_content, section.section_id)

    # Extract legal metadata
    legal_metadata = extract_legal_metadata(section_html, metadata)

    # Get current timestamps
    now = datetime.now(timezone.utc)
    processed_at = now.isoformat()
    ingested_at = metadata.get("ingested_at", now.isoformat())

    # Count tokens (rough approximation)
    token_count = len(normalized_text.split()) if normalized_text else 0

    # Build enhanced metadata
    enhanced = {
        # Original section fields
        "law_id": section.law_id,
        "section_id": section.section_id,
        "path": section.path,
        "heading": section.heading,
        "text_plain": normalized_text,
        "text_html": section_html,  # Only the section HTML, not entire page
        "source_url": section.source_url or metadata.get("url", ""),
        "sha256": stable_hash,
        # Domain and categorization
        "domain": metadata.get("domain", "unknown"),
        "source_type": metadata.get("source_type", "unknown"),
        "publisher": metadata.get("publisher", "unknown"),
        # Versioning and effectiveness
        "version": metadata.get("version", "current"),
        "jurisdiction": metadata.get("jurisdiction", "NO"),
        "effective_from": metadata.get("effective_from", ""),
        "effective_to": metadata.get("effective_to", ""),
        # Legal metadata
        "law_title": legal_metadata.get("law_title", metadata.get("title", "")),
        "chapter": legal_metadata.get("chapter", ""),  # Clean chapter, not concatenated
        "repealed": legal_metadata.get("repealed", False),
        "amended_dates": legal_metadata.get("amended_dates", []),
        # Lineage timestamps
        "ingested_at": ingested_at,
        "processed_at": processed_at,
        # Quality metrics
        "token_count": token_count,
        "crawl_freq": metadata.get("crawl_freq", "unknown"),
    }

    return enhanced


def validate_section_quality(
    section: Dict[str, Any], min_text_length: int = 50
) -> tuple[bool, List[str]]:
    """
    Validate section quality and return issues.

    Args:
        section: Section metadata dictionary
        min_text_length: Minimum required text length

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Check text length
    text_length = len(section.get("text_plain", ""))
    if text_length < min_text_length:
        issues.append(f"Text too short: {text_length} chars (min: {min_text_length})")

    # Check for source URL
    if not section.get("source_url"):
        issues.append("Missing source URL")

    # Check for required fields
    required_fields = ["law_id", "section_id", "domain", "source_type"]
    for field in required_fields:
        if not section.get(field):
            issues.append(f"Missing required field: {field}")

    # Check token count
    token_count = section.get("token_count", 0)
    if token_count == 0 and text_length > 0:
        issues.append("Zero token count for non-empty text")

    # Check for navigation artifacts
    text_plain = section.get("text_plain", "")
    if "🔗" in text_plain or "Del paragraf" in text_plain:
        issues.append("Contains navigation artifacts")

    return len(issues) == 0, issues
