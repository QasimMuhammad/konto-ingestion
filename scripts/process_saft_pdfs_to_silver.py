#!/usr/bin/env python3
"""
Process SAF-T PDFs to Silver layer.
Downloads and parses SAF-T PDF documents to extract detailed technical specifications.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add modules to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.data_io import ensure_data_directories, log, compute_stable_hash
from modules.parsers.saft_pdf_parser import parse_saft_pdfs_from_sources


def process_saft_pdfs_to_silver() -> Dict[str, Any]:
    """Process SAF-T PDFs and write to Silver layer."""
    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    silver_dir = project_root / "data" / "silver"
    
    # Ensure directories exist
    ensure_data_directories()
    
    # Process PDFs
    log.info("Starting SAF-T PDF processing...")
    
    # Sample sources (we'll use the PDF URLs directly)
    sources = [
        {
            "source_id": "saft_v1_30",
            "url": "https://www.skatteetaten.no/en/business-and-organisation/start-and-run/best-practices-accounting-and-cash-register-systems/saf-t-financial/"
        }
    ]
    
    try:
        # Parse PDFs
        nodes = parse_saft_pdfs_from_sources(sources)
        
        if not nodes:
            log.warning("No nodes extracted from PDFs")
            return {"total_nodes": 0, "errors": ["No nodes extracted"]}
        
        # Convert to JSON format
        all_nodes = []
        for node in nodes:
            node_dict = {
                "spec": node.spec,
                "version": node.version,
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
                "examples": node.examples,
                "dependencies": node.dependencies,
                "technical_details": node.technical_details,
                "last_updated": node.last_updated
            }
            all_nodes.append(node_dict)
        
        # Write to Silver layer
        silver_file = silver_dir / "saft_v1_3_nodes.json"
        with open(silver_file, "w", encoding="utf-8") as f:
            json.dump(all_nodes, f, indent=2, ensure_ascii=False)
        
        log.info(f"Wrote {len(all_nodes)} SAF-T nodes to {silver_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("SAF-T PDF PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total nodes extracted: {len(all_nodes)}")
        print(f"File: {silver_file}")
        print("=" * 60)
        
        # Show sample nodes
        print("\nSample nodes:")
        for i, node in enumerate(all_nodes[:3]):
            print(f"\n{i+1}. {node['node_path']}")
            print(f"   Cardinality: {node['cardinality']}")
            print(f"   Data Type: {node['data_type']}")
            print(f"   Description: {node['description'][:80]}...")
        
        return {
            "total_nodes": len(all_nodes),
            "errors": [],
            "file_path": str(silver_file)
        }
        
    except Exception as e:
        log.error(f"Error processing SAF-T PDFs: {e}")
        return {
            "total_nodes": 0,
            "errors": [str(e)]
        }


def main():
    """Main function."""
    result = process_saft_pdfs_to_silver()
    
    if result["errors"]:
        print(f"\nErrors: {result['errors']}")
        sys.exit(1)
    else:
        print(f"\nSuccessfully processed {result['total_nodes']} SAF-T nodes")


if __name__ == "__main__":
    main()
