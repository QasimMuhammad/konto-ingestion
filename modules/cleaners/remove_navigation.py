"""
Remove navigation artifacts from legal text.
"""

import re


def remove_navigation_artifacts(text: str) -> str:
    """
    Remove navigation artifacts and unwanted elements from legal text.
    
    Args:
        text: Raw legal text content
        
    Returns:
        Cleaned legal text without navigation elements
    """
    if not text:
        return ""
    
    # Remove navigation elements and links
    text = re.sub(r'🔗\s*Del paragraf', '', text)
    text = re.sub(r'🔗\s*.*', '', text)  # Remove any other link symbols
    text = re.sub(r'Se også.*', '', text)  # Remove "See also" references
    text = re.sub(r'Gå til.*', '', text)  # Remove "Go to" references
    
    # Remove common Lovdata navigation elements
    text = re.sub(r'\[Til toppen\]', '', text)
    text = re.sub(r'\[Tilbake\]', '', text)
    text = re.sub(r'\[Neste\]', '', text)
    text = re.sub(r'\[Forrige\]', '', text)
    
    # Remove any remaining navigation patterns
    text = re.sub(r'🔗.*', '', text)  # Remove any remaining link symbols
    text = re.sub(r'→.*', '', text)  # Remove arrow navigation
    text = re.sub(r'←.*', '', text)  # Remove back arrow navigation
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text
