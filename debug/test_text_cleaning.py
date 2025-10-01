#!/usr/bin/env python3
"""
Test text cleaning to show the difference.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.cleaners.improved_text_processing import clean_legal_text, normalize_text

def test_text_cleaning():
    """Test the text cleaning functions."""
    
    # Sample text with navigation artifacts
    sample_text = "§ 1-2. Geografisk virkeområde (1) Denne loven får anvendelse i merverdiavgiftsområdet. (2) Med merverdiavgiftsområdet menes det norske fastlandet og alt område innenfor territorialgrensen, men ikke Svalbard, Jan Mayen eller de norske bilandene. 🔗 Del paragraf"
    
    print("Original text:")
    print(f"'{sample_text}'")
    print()
    
    # Clean the text
    cleaned_text = clean_legal_text(sample_text)
    print("After clean_legal_text:")
    print(f"'{cleaned_text}'")
    print()
    
    # Normalize the text
    normalized_text = normalize_text(cleaned_text)
    print("After normalize_text:")
    print(f"'{normalized_text}'")
    print()
    
    # Show the difference
    print("Difference:")
    print(f"Removed: '{sample_text[len(normalized_text):]}'")
    
    return 0

if __name__ == "__main__":
    sys.exit(test_text_cleaning())
