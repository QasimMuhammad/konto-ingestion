"""
Domain-specific pipeline implementations.
"""

from typing import List, Dict, Any
from pathlib import Path

from .ingestion_pipeline import IngestionPipeline, fetch_html_source
from .processing_pipeline import ProcessingPipeline
from ..data_io import log


class TaxIngestionPipeline(IngestionPipeline):
    """Pipeline for ingesting tax regulations."""

    def __init__(self):
        super().__init__("tax_ingestion", fetch_html_source)

    def get_sources_to_process(self) -> List[Dict[str, str]]:
        """Get tax sources to process."""
        if self.source_loader is None:
            raise RuntimeError("SourceLoader not initialized")
        return self.source_loader.filter_by_domain("tax")


class AccountingIngestionPipeline(IngestionPipeline):
    """Pipeline for ingesting accounting regulations."""

    def __init__(self):
        super().__init__("accounting_ingestion", fetch_html_source)

    def get_sources_to_process(self) -> List[Dict[str, str]]:
        """Get accounting sources to process."""
        if self.source_loader is None:
            raise RuntimeError("SourceLoader not initialized")
        return self.source_loader.filter_by_domain("accounting")


class ReportingIngestionPipeline(IngestionPipeline):
    """Pipeline for ingesting reporting regulations."""

    def __init__(self):
        super().__init__("reporting_ingestion", fetch_html_source)

    def get_sources_to_process(self) -> List[Dict[str, str]]:
        """Get reporting sources to process."""
        if self.source_loader is None:
            raise RuntimeError("SourceLoader not initialized")
        return self.source_loader.filter_by_domain("reporting")


class RatesProcessingPipeline(ProcessingPipeline):
    """Pipeline for processing VAT rates."""

    def __init__(self):
        super().__init__("rates_processing", self._process_rates_sources)

    def get_sources_to_process(self) -> List[Dict[str, str]]:
        """Get rates sources to process."""
        if self.source_loader is None:
            raise RuntimeError("SourceLoader not initialized")
        return self.source_loader.filter_by_source_type("rates")

    def _process_rates_sources(
        self, sources: List[Dict[str, str]], bronze_dir: Path, silver_dir: Path
    ) -> Dict[str, Any]:
        """Process VAT rates sources."""
        from ..parsers.rates_parser import parse_mva_rates

        stats: dict[str, Any] = {
            "total_sources": len(sources),
            "processed_sources": 0,
            "total_rates": 0,
            "errors": [],
        }

        all_rates: list[Any] = []

        for source in sources:
            source_id = source["source_id"]
            file_path = bronze_dir / f"{source_id}.html"

            if not file_path.exists():
                stats["errors"].append(f"Bronze file not found: {file_path}")
                continue

            try:
                # Parse rates from HTML
                html_content = file_path.read_text(encoding="utf-8")
                # Compute actual SHA256 hash
                from ..hash_utils import compute_stable_hash

                sha256_hash = compute_stable_hash(html_content)
                rates = parse_mva_rates(html_content, source["url"], sha256_hash)

                # Convert to dict format for JSON serialization
                rate_dicts = []
                for rate in rates:
                    rate_dict = {
                        "kind": rate.kind,
                        "percentage": rate.percentage,
                        "description": rate.description,
                        "category": rate.category,
                        "applies_to": rate.applies_to,
                        "exceptions": rate.exceptions,
                        "notes": rate.notes,
                        "source_url": rate.source_url,
                        "sha256": rate.sha256,
                        "publisher": rate.publisher,
                        "jurisdiction": "NO",  # Default jurisdiction
                        "is_current": rate.is_current,
                        "last_updated": rate.last_updated,
                    }
                    rate_dicts.append(rate_dict)

                all_rates.extend(rate_dicts)
                stats["processed_sources"] += 1
                stats["total_rates"] += len(rate_dicts)

                log.info(f"Processed {source_id}: {len(rate_dicts)} rates")

            except Exception as e:
                error_msg = f"Error processing {source_id}: {str(e)}"
                stats["errors"].append(error_msg)
                log.error(error_msg)

        # Save to silver layer
        if all_rates:
            self.save_results("rate_table.json", all_rates)

        return stats


class AmeldingProcessingPipeline(ProcessingPipeline):
    """Pipeline for processing A-meldingen rules."""

    def __init__(self):
        super().__init__("amelding_processing", self._process_amelding_sources)

    def get_sources_to_process(self) -> List[Dict[str, str]]:
        """Get A-meldingen sources to process."""
        if self.source_loader is None:
            raise RuntimeError("SourceLoader not initialized")
        return self.source_loader.filter_by_source_id_pattern("amelding")

    def _process_amelding_sources(
        self, sources: List[Dict[str, str]], bronze_dir: Path, silver_dir: Path
    ) -> Dict[str, Any]:
        """Process A-meldingen sources."""
        from ..parsers.amelding_parser import (
            parse_amelding_overview,
            parse_amelding_forms,
        )

        stats: dict[str, Any] = {
            "total_sources": len(sources),
            "processed_sources": 0,
            "total_rules": 0,
            "errors": [],
        }

        all_rules: list[Any] = []

        for source in sources:
            source_id = source["source_id"]
            file_path = bronze_dir / f"{source_id}.html"

            if not file_path.exists():
                stats["errors"].append(f"Bronze file not found: {file_path}")
                continue

            try:
                # Parse rules from HTML
                html_content = file_path.read_text(encoding="utf-8")

                if "overview" in source_id.lower():
                    rules = parse_amelding_overview(
                        html_content, source["url"], "bronze_hash"
                    )
                elif "forms" in source_id.lower():
                    rules = parse_amelding_forms(
                        html_content, source["url"], "bronze_hash"
                    )
                else:
                    # Try both parsers
                    rules = parse_amelding_overview(
                        html_content, source["url"], "bronze_hash"
                    )
                    rules.extend(
                        parse_amelding_forms(html_content, source["url"], "bronze_hash")
                    )

                # Convert to dict format for JSON serialization
                rule_dicts = []
                for rule in rules:
                    rule_dict = {
                        "rule_id": rule.rule_id,
                        "title": rule.title,
                        "description": rule.description,
                        "category": rule.category,
                        "source_url": rule.source_url,
                        "sha256": rule.sha256,
                        "domain": rule.domain,
                        "source_type": rule.source_type,
                        "publisher": rule.publisher,
                        "jurisdiction": rule.jurisdiction,
                        "is_current": rule.is_current,
                        "effective_from": rule.effective_from,
                        "effective_to": rule.effective_to,
                        "priority": rule.priority,
                        "complexity": rule.complexity,
                        "technical_details": rule.technical_details,
                        "validation_rules": rule.validation_rules,
                        "field_mappings": rule.field_mappings,
                        "business_rules": rule.business_rules,
                        "last_updated": rule.last_updated,
                    }
                    rule_dicts.append(rule_dict)

                all_rules.extend(rule_dicts)
                stats["processed_sources"] += 1
                stats["total_rules"] += len(rule_dicts)

                log.info(f"Processed {source_id}: {len(rule_dicts)} rules")

            except Exception as e:
                error_msg = f"Error processing {source_id}: {str(e)}"
                stats["errors"].append(error_msg)
                log.error(error_msg)

        # Save to silver layer
        if all_rules:
            self.save_results("amelding_rules.json", all_rules)

        return stats


class SaftProcessingPipeline(ProcessingPipeline):
    """Pipeline for processing SAF-T specifications."""

    def __init__(self):
        super().__init__("saft_processing", self._process_saft_sources)

    def get_sources_to_process(self) -> List[Dict[str, str]]:
        """Get SAF-T sources to process."""
        if self.source_loader is None:
            raise RuntimeError("SourceLoader not initialized")
        return self.source_loader.filter_by_source_id_pattern("saft")

    def _process_saft_sources(
        self, sources: List[Dict[str, str]], bronze_dir: Path, silver_dir: Path
    ) -> Dict[str, Any]:
        """Process SAF-T sources."""
        from ..parsers.saft_parser import parse_saft_documentation

        stats: dict[str, Any] = {
            "total_sources": len(sources),
            "processed_sources": 0,
            "total_nodes": 0,
            "errors": [],
        }

        all_nodes: list[Any] = []

        for source in sources:
            source_id = source["source_id"]
            file_path = bronze_dir / f"{source_id}.html"

            if not file_path.exists():
                stats["errors"].append(f"Bronze file not found: {file_path}")
                continue

            try:
                # Parse SAF-T nodes from HTML
                html_content = file_path.read_text(encoding="utf-8")
                nodes = parse_saft_documentation(
                    html_content, "1.30", source["url"], "bronze_hash"
                )

                # Convert to dict format for JSON serialization
                node_dicts = []
                for node in nodes:
                    node_dict = {
                        "node_path": node.node_path,
                        "cardinality": node.cardinality,
                        "description": node.description,
                        "source_url": node.source_url,
                        "sha256": node.sha256,
                        "domain": node.domain,
                        "source_type": node.source_type,
                        "publisher": node.publisher,
                        "jurisdiction": node.jurisdiction,
                        "is_current": node.is_current,
                        "effective_from": node.effective_from,
                        "effective_to": node.effective_to,
                        "priority": node.priority,
                        "complexity": node.complexity,
                        "data_type": node.data_type,
                        "format": node.format,
                        "validation_rules": node.validation_rules,
                        "business_rules": node.business_rules,
                        "dependencies": node.dependencies,
                        "technical_details": node.technical_details,
                        "last_updated": node.last_updated,
                    }
                    node_dicts.append(node_dict)

                all_nodes.extend(node_dicts)
                stats["processed_sources"] += 1
                stats["total_nodes"] += len(node_dicts)

                log.info(f"Processed {source_id}: {len(node_dicts)} nodes")

            except Exception as e:
                error_msg = f"Error processing {source_id}: {str(e)}"
                stats["errors"].append(error_msg)
                log.error(error_msg)

        # Save to silver layer
        if all_nodes:
            self.save_results("saft_v1_3_nodes.json", all_nodes)

        return stats


class LegalTextProcessingPipeline(ProcessingPipeline):
    """Pipeline for processing legal texts (laws and regulations)."""

    def __init__(self):
        super().__init__("legal_text_processing", self._process_legal_sources)

    def get_sources_to_process(self) -> List[Dict[str, str]]:
        """Get legal text sources to process (law and forskrift types)."""
        if self.source_loader is None:
            raise RuntimeError("SourceLoader not initialized")
        all_sources = self.source_loader.load_all_sources()
        return [
            s for s in all_sources if s.get("source_type", "") in ["law", "forskrift"]
        ]

    def _process_legal_sources(
        self, sources: List[Dict[str, str]], bronze_dir: Path, silver_dir: Path
    ) -> Dict[str, Any]:
        """Process legal text sources."""
        from ..parsers.lovdata_parser import parse_lovdata_html
        from ..cleaners.legal_text_cleaner import (
            clean_legal_text,
            normalize_text,
            compute_stable_hash,
            extract_legal_metadata,
        )

        stats: dict[str, Any] = {
            "total_sources": len(sources),
            "processed_sources": 0,
            "total_sections": 0,
            "errors": [],
        }

        all_sections: list[Any] = []

        for source in sources:
            source_id = source["source_id"]
            file_path = bronze_dir / f"{source_id}.html"

            if not file_path.exists():
                stats["errors"].append(f"Bronze file not found: {file_path}")
                continue

            try:
                html_content = file_path.read_text(encoding="utf-8")
                sections = parse_lovdata_html(
                    html_content, source_id, source["url"], "bronze_hash"
                )

                for section in sections:
                    section_dict: dict[str, Any] = {
                        "law_id": section.law_id,
                        "section_id": section.section_id,
                        "section_label": getattr(section, "section_label", ""),
                        "path": section.path,
                        "heading": section.heading,
                        "text_plain": clean_legal_text(
                            normalize_text(section.text_plain)
                        ),
                        "source_url": section.source_url,
                        "sha256": compute_stable_hash(section.text_plain),
                        "domain": source.get("domain", ""),
                        "source_type": source.get("source_type", ""),
                        "publisher": source.get("publisher", ""),
                        "version": source.get("version", "current"),
                        "jurisdiction": source.get("jurisdiction", "NO"),
                        "effective_from": source.get("effective_from") or None,
                        "effective_to": source.get("effective_to") or None,
                        "law_title": source.get("title", ""),
                        "is_current": True,
                    }

                    enriched_metadata = extract_legal_metadata(
                        html_content,
                        section_dict,
                        section_heading=section.heading,
                        section_path=section.path,
                        cleaned_text=section_dict["text_plain"],
                    )
                    section_dict.update(enriched_metadata)

                    all_sections.append(section_dict)

                stats["processed_sources"] += 1
                stats["total_sections"] += len(sections)
                log.info(f"Processed {source_id}: {len(sections)} sections")

            except Exception as e:
                error_msg = f"Error processing {source_id}: {str(e)}"
                stats["errors"].append(error_msg)
                log.error(error_msg)

        if all_sections:
            self.save_results("law_sections.json", all_sections)

        return stats
