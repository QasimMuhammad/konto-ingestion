"""
Source loader component for loading and filtering sources from CSV.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from ..data_io import log


class SourceLoader:
    """Component for loading and filtering sources from CSV."""
    
    def __init__(self, sources_file: Path):
        self.sources_file = sources_file
        self._sources_cache: Optional[List[Dict[str, str]]] = None
    
    def load_all_sources(self) -> List[Dict[str, str]]:
        """Load all sources from CSV file."""
        if self._sources_cache is not None:
            return self._sources_cache
        
        sources = []
        
        if not self.sources_file.exists():
            log.error(f"Sources file not found: {self.sources_file}")
            return sources
        
        try:
            with open(self.sources_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sources.append(row)
            
            log.info(f"Loaded {len(sources)} sources from {self.sources_file}")
            self._sources_cache = sources
            
        except Exception as e:
            log.error(f"Failed to load sources from {self.sources_file}: {e}")
        
        return sources
    
    def filter_by_domain(self, domain: str) -> List[Dict[str, str]]:
        """Filter sources by domain."""
        all_sources = self.load_all_sources()
        return [
            source for source in all_sources 
            if source.get("domain", "").lower() == domain.lower()
        ]
    
    def filter_by_source_type(self, source_type: str) -> List[Dict[str, str]]:
        """Filter sources by source type."""
        all_sources = self.load_all_sources()
        return [
            source for source in all_sources 
            if source.get("source_type", "").lower() == source_type.lower()
        ]
    
    def filter_by_publisher(self, publisher: str) -> List[Dict[str, str]]:
        """Filter sources by publisher."""
        all_sources = self.load_all_sources()
        return [
            source for source in all_sources 
            if source.get("publisher", "").lower() == publisher.lower()
        ]
    
    def filter_by_crawl_frequency(self, frequency: str) -> List[Dict[str, str]]:
        """Filter sources by crawl frequency."""
        all_sources = self.load_all_sources()
        return [
            source for source in all_sources 
            if source.get("crawl_freq", "").lower() == frequency.lower()
        ]
    
    def filter_by_source_id_pattern(self, pattern: str) -> List[Dict[str, str]]:
        """Filter sources by source ID pattern."""
        all_sources = self.load_all_sources()
        return [
            source for source in all_sources 
            if pattern.lower() in source.get("source_id", "").lower()
        ]
    
    def filter_by_custom(self, filter_func: Callable[[Dict[str, str]], bool]) -> List[Dict[str, str]]:
        """Filter sources using a custom filter function."""
        all_sources = self.load_all_sources()
        return [source for source in all_sources if filter_func(source)]
    
    def get_source_by_id(self, source_id: str) -> Optional[Dict[str, str]]:
        """Get a specific source by ID."""
        all_sources = self.load_all_sources()
        for source in all_sources:
            if source.get("source_id", "") == source_id:
                return source
        return None
    
    def get_sources_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Get sources as a lookup dictionary by source_id."""
        all_sources = self.load_all_sources()
        lookup = {}
        
        for source in all_sources:
            source_id = source.get("source_id", "")
            if source_id:
                lookup[source_id] = source
        
        return lookup
    
    def clear_cache(self) -> None:
        """Clear the sources cache."""
        self._sources_cache = None
