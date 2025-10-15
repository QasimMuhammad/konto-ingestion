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

    text = re.sub(r"🔗\s*Del paragraf", "", text)
    text = re.sub(r"🔗\s*.*", "", text)
    text = re.sub(r"Se også.*", "", text)
    text = re.sub(r"Gå til.*", "", text)

    text = re.sub(r"\[Til toppen\]", "", text)
    text = re.sub(r"\[Tilbake\]", "", text)
    text = re.sub(r"\[Neste\]", "", text)
    text = re.sub(r"\[Forrige\]", "", text)

    text = re.sub(r"Rettskilder.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Business and organisation.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Hovedmeny.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Navigasjon.*", "", text, flags=re.IGNORECASE)

    text = re.sub(r"Endret ved.*?🔗Del paragraf", "", text)
    text = re.sub(r"Endret ved.*?$", "", text)

    text = re.sub(r"<svg[^>]*>.*?</svg>", "", text, flags=re.DOTALL)
    text = re.sub(r"<img[^>]*>", "", text)
    text = re.sub(r"<a[^>]*>.*?</a>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)

    text = re.sub(r"Del paragraf|🔗", "", text)
    text = re.sub(r"^\d+\s+", "", text)
    text = re.sub(r"\s+\d+\s*$", "", text)
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

    section_element = None

    if section_id:
        section_element = soup.find(id=section_id)

    if not section_element:
        section_element = soup.find("div", class_="paragraf")

    if not section_element:
        section_element = soup.find("div", class_="document-content")

    if not section_element:
        section_element = soup.find("main")

    if not section_element:
        section_element = soup.find("body")

    if section_element:
        if hasattr(section_element, "find_all"):
            nav_elements = section_element.find_all(
                ["nav", "header", "footer", "aside"]
            )
            for element in nav_elements:
                if hasattr(element, "decompose"):
                    element.decompose()

            script_elements = section_element.find_all(["script", "style"])
            for element in script_elements:
                if hasattr(element, "decompose"):
                    element.decompose()

        if hasattr(section_element, "find_all"):
            for element in section_element.find_all("a", href=True):
                if "del-paragraf" in element.get("href", "").lower():
                    if hasattr(element, "decompose"):
                        element.decompose()

        return str(section_element)

    body = soup.find("body")
    if body:
        if hasattr(body, "find_all"):
            unwanted_elements = body.find_all(
                ["script", "style", "nav", "header", "footer"]
            )
            for element in unwanted_elements:
                if hasattr(element, "decompose"):
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

    soup = BeautifulSoup(text, "html.parser")

    for script in soup(["script", "style"]):
        script.decompose()

    text_content = soup.get_text()
    text_content = clean_legal_text(text_content)
    text_content = re.sub(r"\s+", " ", text_content)
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

    canonical = text.lower().strip()
    canonical = re.sub(r"\s+", " ", canonical)
    canonical = canonical.encode("utf-8").decode("unicode_escape")

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def extract_legal_metadata(
    html_content: str,
    metadata: Dict[str, Any],
    section_heading: str = "",
    section_path: str = "",
    cleaned_text: str = "",
) -> Dict[str, Any]:
    """
    Extract legal metadata from HTML content with improved parsing.

    Args:
        html_content: Raw HTML content
        metadata: Existing metadata dictionary

    Returns:
        Dictionary with extracted legal metadata
    """
    soup = BeautifulSoup(html_content, "html.parser")

    legal_metadata: dict[str, Any] = {}

    # Extract law title - prioritize h1 over title, and clean it properly
    law_title = ""

    # Try h1 first (usually the main law title)
    h1_elem = soup.select_one("h1")
    if h1_elem:
        law_title = h1_elem.get_text().strip()
        # Clean up common patterns
        law_title = re.sub(r"\s*-\s*(Lovdata|Skatteetaten|Altinn)", "", law_title)
        law_title = re.sub(
            r"\s*\([^)]*\)\s*$", "", law_title
        )  # Remove trailing parentheticals
        law_title = re.sub(
            r"\s*\[[^\]]*\]\s*$", "", law_title
        )  # Remove trailing brackets

    # If h1 is empty or looks like menu text, try title tag
    if not law_title or law_title.lower() in ["hovedmeny", "main menu", "navigasjon"]:
        title_elem = soup.select_one("title")
        if title_elem:
            title_text = title_elem.get_text().strip()
            # Extract the law name from title (usually before the first dash)
            title_parts = title_text.split(" - ")
            if len(title_parts) > 1:
                law_title = title_parts[0].strip()
            else:
                law_title = title_text

    # Fallback to metadata title if still empty
    if not law_title:
        law_title = metadata.get("title", "")

    legal_metadata["law_title"] = law_title

    # Extract chapter information from section path (most reliable)
    chapter_no = ""
    chapter_title = ""

    # Try to extract chapter from the section's path first
    if section_path:
        # Pattern: "Kapittel 5 PARAGRAF_3-1" -> extract "5"
        path_match = re.match(r"Kapittel\s+(\d+)\s+", section_path)
        if path_match:
            chapter_no = path_match.group(1).strip()

    # If no chapter from path, try to find it in the HTML
    if not chapter_no:
        chapter_selectors = [
            "h2:-soup-contains('Kapittel')",
            "h3:-soup-contains('Kapittel')",
            ".chapter h2",
            ".kapittel h2",
            "h2[class*='chapter']",
            "h2[class*='kapittel']",
        ]

        for selector in chapter_selectors:
            try:
                chapter_elem = soup.select_one(selector)
                if chapter_elem:
                    chapter_text = chapter_elem.get_text().strip()
                    # Extract chapter number and title
                    chapter_match = re.match(
                        r"Kapittel\s+(\d+)[\s\.]*([^§]*?)(?:§|$)", chapter_text
                    )
                    if chapter_match:
                        chapter_no = chapter_match.group(1).strip()
                        chapter_title = chapter_match.group(2).strip()
                        # Clean up the title
                        chapter_title = re.sub(r"\s+", " ", chapter_title)
                        chapter_title = re.sub(
                            r"\.$", "", chapter_title
                        )  # Remove trailing period
                        break
            except Exception:
                continue

    # Store clean chapter info
    legal_metadata["chapter_no"] = chapter_no
    legal_metadata["chapter_title"] = chapter_title
    if chapter_no and chapter_title:
        legal_metadata["chapter"] = f"Kapittel {chapter_no}. {chapter_title}"
    elif chapter_no:
        legal_metadata["chapter"] = f"Kapittel {chapter_no}"

    # Check for repealed status - look for explicit repeal markers
    is_repealed = False
    repeal_date = None

    # Check if heading contains "(Opphevet)" - this is a clear repeal indicator
    if section_heading and "(Opphevet)" in section_heading:
        is_repealed = True
        # Try to extract repeal date from the cleaned text content
        section_text = cleaned_text if cleaned_text else soup.get_text()

        # Look for "ikr." (i kraft) followed by date - case insensitive
        ikr_match = re.search(
            r"ikr\.\s+(\d{1,2}\s+\w+\s+\d{4})", section_text, re.IGNORECASE
        )
        if ikr_match:
            repeal_date = ikr_match.group(1)
        else:
            # Look for "i kraft" followed by date
            ikraft_match = re.search(
                r"i\s+kraft\s+(\d{1,2}\s+\w+\s+\d{4})", section_text, re.IGNORECASE
            )
            if ikraft_match:
                repeal_date = ikraft_match.group(1)
            else:
                # Fallback: look for any date in the text
                date_match = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", section_text)
                if date_match:
                    repeal_date = date_match.group(1)

    # Also check page title for repeal indicators
    if not is_repealed:
        page_title = soup.select_one("title, h1")
        if page_title:
            page_title_text = page_title.get_text().lower()
            if "opphevet" in page_title_text and (
                "ved" in page_title_text or "forskrift" in page_title_text
            ):
                is_repealed = True
                # Try to extract repeal date from title
                date_match = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", page_title_text)
                if date_match:
                    repeal_date = date_match.group(1)

    legal_metadata["repealed"] = is_repealed
    if repeal_date:
        # Normalize repeal date to ISO format
        normalized_repeal_date = normalize_norwegian_date(repeal_date)
        legal_metadata["repeal_date"] = normalized_repeal_date

    # Extract amendment dates with better parsing
    page_text = soup.get_text().lower()
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
        # Normalize dates to ISO format and structure as amendments array
        normalized_amendments = []
        for date_str in set(amendments):  # Remove duplicates
            normalized_date = normalize_norwegian_date(date_str)
            normalized_amendments.append(
                {"date": normalized_date, "note": f"Amended {date_str}"}
            )
        legal_metadata["amendments"] = normalized_amendments
    else:
        legal_metadata["amendments"] = []

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


def normalize_norwegian_date(date_str: str) -> str:
    """Convert Norwegian date to ISO format (YYYY-MM-DD)."""
    if not date_str:
        return ""

    # Norwegian month names to numbers
    month_map = {
        "jan": "01",
        "januar": "01",
        "feb": "02",
        "februar": "02",
        "mar": "03",
        "mars": "03",
        "apr": "04",
        "april": "04",
        "mai": "05",
        "jun": "06",
        "juni": "06",
        "jul": "07",
        "juli": "07",
        "aug": "08",
        "august": "08",
        "sep": "09",
        "september": "09",
        "okt": "10",
        "oktober": "10",
        "nov": "11",
        "november": "11",
        "des": "12",
        "desember": "12",
    }

    # Pattern: "1 jan 2021" or "16 juni 2023"
    match = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", date_str.strip())
    if match:
        day, month, year = match.groups()
        month_num = month_map.get(month.lower())
        if month_num:
            return f"{year}-{month_num}-{day.zfill(2)}"

    return date_str  # Return original if can't parse
