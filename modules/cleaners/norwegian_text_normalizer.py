"""
Text normalization utilities for Norwegian legal documents.
Handles encoding, whitespace, and special characters.
"""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize text content for consistent processing.

    Args:
        text: Raw text content

    Returns:
        Normalized text with proper encoding and whitespace
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u00A0\u2000-\u200F\u2028-\u202F\u205F\u3000]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    text = _fix_norwegian_encoding(text)

    return text


def _fix_norwegian_encoding(text: str) -> str:
    """Fix common Norwegian character encoding issues."""
    replacements = {
        "Ã¦": "æ",
        "Ã¸": "ø",
        "Ã¥": "å",
        "Ã†": "Æ",
        "Ã˜": "Ø",
        "Ã…": "Å",
        "Ã©": "é",
        "Ã¨": "è",
        "Ã¡": "á",
        "Ã­": "í",
        "Ã³": "ó",
        "Ãº": "ú",
        "Ã¼": "ü",
        "Ã¤": "ä",
        "Ã¶": "ö",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text


def clean_section_text(text: str) -> str:
    """
    Clean section text by removing footnotes and references.

    Args:
        text: Raw section text

    Returns:
        Cleaned text with footnotes removed
    """
    if not text:
        return ""

    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\(\d+\)", "", text)
    text = re.sub(r"jf\.\s*[^.]*\.", "", text)
    text = re.sub(r"se\s*[^.]*\.", "", text)
    text = normalize_text(text)

    return text


def extract_citations(text: str) -> list[str]:
    """
    Extract legal citations from text.

    Args:
        text: Text content to search for citations

    Returns:
        List of found citations
    """
    citations = []

    lovdata_pattern = r"lov-\d{4}-\d{2}-\d{2}-\d+"
    citations.extend(re.findall(lovdata_pattern, text))

    section_pattern = r"§\s*\d+-\d+"
    citations.extend(re.findall(section_pattern, text))

    law_pattern = r"[A-ZÆØÅ][a-zæøå]*-loven"
    citations.extend(re.findall(law_pattern, text))

    return list(set(citations))
