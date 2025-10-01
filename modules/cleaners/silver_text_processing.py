"""
Text processing utilities for Silver layer data.
Handles HTML cleaning, text normalization, and metadata extraction.
"""

import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any
from bs4 import BeautifulSoup


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

    # Extract chapter information
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
    Enhance section with comprehensive metadata.

    Args:
        section: Section object from parser
        metadata: Source metadata dictionary
        html_content: Raw HTML content

    Returns:
        Enhanced section metadata dictionary
    """
    # Normalize text content
    normalized_text = normalize_text(section.text_plain)

    # Compute stable hash
    stable_hash = compute_stable_hash(normalized_text)

    # Extract legal metadata
    legal_metadata = extract_legal_metadata(html_content, metadata)

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
        "text_html": html_content,  # Keep raw HTML for citation rendering
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
        "chapter": legal_metadata.get("chapter", ""),
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


def clean_html_for_display(html_content: str) -> str:
    """
    Clean HTML content for display purposes.

    Args:
        html_content: Raw HTML content

    Returns:
        Cleaned HTML suitable for display
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove unwanted elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Clean up classes and attributes
    for tag in soup.find_all():
        # Remove most attributes except essential ones
        attrs_to_keep = ["href", "src", "alt", "title"]
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in attrs_to_keep}

    return str(soup)


def extract_text_preview(text: str, max_length: int = 200) -> str:
    """
    Extract a preview of text content.

    Args:
        text: Full text content
        max_length: Maximum length of preview

    Returns:
        Text preview with ellipsis if truncated
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    # Find a good break point (end of sentence or word)
    preview = text[:max_length]
    last_period = preview.rfind(".")
    last_space = preview.rfind(" ")

    break_point = max(last_period, last_space)
    if break_point > max_length * 0.7:  # Only use break point if it's not too short
        preview = preview[: break_point + 1]

    return preview + "..."


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

    return len(issues) == 0, issues
