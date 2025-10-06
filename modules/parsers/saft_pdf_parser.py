#!/usr/bin/env python3
"""
SAF-T PDF parser.
Extracts detailed technical specifications from SAF-T PDF documents.
"""

import re
import io
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import requests
from datetime import datetime

try:
    import fitz  # PyMuPDF
    import pdfplumber
    from PyPDF2 import PdfReader
except ImportError:
    print("PDF parsing libraries not available. Install with: uv add PyPDF2 pdfplumber pymupdf")
    raise


@dataclass
class SpecNode:
    """SAF-T specification node with detailed information."""
    spec: str
    version: str
    node_path: str
    cardinality: str
    description: str
    source_url: str
    sha256: str
    domain: str = "tax"
    source_type: str = "specification"
    publisher: str = "Skatteetaten"
    jurisdiction: str = "NO"
    is_current: bool = True
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    priority: str = "medium"
    complexity: str = "medium"
    last_updated: str = datetime.now().isoformat()
    data_type: str = ""
    format: str = ""
    validation_rules: List[str] = None
    business_rules: List[str] = None
    examples: List[str] = None
    dependencies: List[str] = None
    technical_details: List[str] = None
    
    def __post_init__(self):
        if self.validation_rules is None:
            self.validation_rules = []
        if self.business_rules is None:
            self.business_rules = []
        if self.examples is None:
            self.examples = []
        if self.dependencies is None:
            self.dependencies = []
        if self.technical_details is None:
            self.technical_details = []


class SAFTPDFParser:
    """Parser for SAF-T PDF documents."""
    
    def __init__(self):
        self.nodes: List[SpecNode] = []
        self.current_version = "1.30"
        
    def download_pdf(self, url: str, filename: str) -> Optional[Path]:
        """Download PDF from URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Create bronze directory for PDFs
            bronze_dir = Path("data/bronze")
            bronze_dir.mkdir(parents=True, exist_ok=True)
            
            pdf_path = bronze_dir / f"{filename}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(response.content)
                
            return pdf_path
        except Exception as e:
            print(f"Failed to download PDF {url}: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF using multiple methods."""
        text = ""
        
        # Method 1: PyMuPDF (fitz) - best for structured text
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            print(f"PyMuPDF failed: {e}")
        
        # Method 2: pdfplumber - good for tables and structured content
        if not text.strip():
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"pdfplumber failed: {e}")
        
        # Method 3: PyPDF2 - fallback
        if not text.strip():
            try:
                with open(pdf_path, "rb") as file:
                    reader = PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                print(f"PyPDF2 failed: {e}")
        
        return text
    
    def extract_tables_from_pdf(self, pdf_path: Path) -> List[List[List[str]]]:
        """Extract tables from PDF."""
        tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        except Exception as e:
            print(f"Table extraction failed: {e}")
        return tables
    
    def parse_technical_description_pdf(self, pdf_path: Path, source_url: str, sha256: str) -> List[SpecNode]:
        """Parse the technical description PDF."""
        text = self.extract_text_from_pdf(pdf_path)
        tables = self.extract_tables_from_pdf(pdf_path)
        
        nodes = []
        
        # Focus on table extraction - the real data is in tables
        for table in tables:
            table_nodes = self._extract_nodes_from_table(table, source_url, sha256)
            if table_nodes:  # Only add if we found actual nodes
                nodes.extend(table_nodes)
        
        # Only use text patterns as fallback for very specific cases
        if not nodes:
            nodes.extend(self._extract_nodes_from_text(text, source_url, sha256))
        
        return nodes
    
    def parse_header_pdf(self, pdf_path: Path, source_url: str, sha256: str) -> List[SpecNode]:
        """Parse the header PDF."""
        text = self.extract_text_from_pdf(pdf_path)
        return self._extract_nodes_from_text(text, source_url, sha256, prefix="Header")
    
    def parse_masterfiles_pdf(self, pdf_path: Path, source_url: str, sha256: str) -> List[SpecNode]:
        """Parse the masterfiles PDF."""
        text = self.extract_text_from_pdf(pdf_path)
        return self._extract_nodes_from_text(text, source_url, sha256, prefix="MasterFiles")
    
    def parse_generalledger_pdf(self, pdf_path: Path, source_url: str, sha256: str) -> List[SpecNode]:
        """Parse the general ledger entries PDF."""
        text = self.extract_text_from_pdf(pdf_path)
        return self._extract_nodes_from_text(text, source_url, sha256, prefix="GeneralLedgerEntries")
    
    def _extract_nodes_from_text(self, text: str, source_url: str, sha256: str, prefix: str = "") -> List[SpecNode]:
        """Extract nodes from text content."""
        nodes = []
        
        # Pattern 1: Element definitions with cardinality
        element_pattern = r'(\w+(?:\.\w+)*)\s*\(([0-9*.,]+)\)\s*:\s*(.+?)(?=\n\w|\n\n|$)'
        matches = re.findall(element_pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            node_path, cardinality, description = match
            if prefix and not node_path.startswith(prefix):
                node_path = f"{prefix}.{node_path}"
            
            node = self._create_node_from_text(
                node_path.strip(),
                cardinality.strip(),
                description.strip(),
                source_url,
                sha256
            )
            if node:
                nodes.append(node)
        
        # Pattern 2: XML element patterns
        xml_pattern = r'<(\w+(?:\.\w+)*)\s*([^>]*)>\s*(.*?)(?=<|$)'
        xml_matches = re.findall(xml_pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in xml_matches:
            node_path, attributes, content = match
            if prefix and not node_path.startswith(prefix):
                node_path = f"{prefix}.{node_path}"
            
            # Extract cardinality from attributes
            cardinality = "1..1"  # Default
            if "minOccurs" in attributes and "maxOccurs" in attributes:
                min_occurs = re.search(r'minOccurs="([^"]*)"', attributes)
                max_occurs = re.search(r'maxOccurs="([^"]*)"', attributes)
                if min_occurs and max_occurs:
                    min_val = min_occurs.group(1)
                    max_val = max_occurs.group(1)
                    if max_val == "unbounded":
                        cardinality = f"{min_val}..*"
                    else:
                        cardinality = f"{min_val}..{max_val}"
            
            node = self._create_node_from_text(
                node_path.strip(),
                cardinality,
                content.strip(),
                source_url,
                sha256
            )
            if node:
                nodes.append(node)
        
        # Pattern 3: Table-like structures in text
        table_pattern = r'(\w+(?:\.\w+)*)\s*\|\s*([0-9*.,]+)\s*\|\s*(.+?)(?=\n\w|\n\n|$)'
        table_matches = re.findall(table_pattern, text, re.MULTILINE)
        
        for match in table_matches:
            node_path, cardinality, description = match
            if prefix and not node_path.startswith(prefix):
                node_path = f"{prefix}.{node_path}"
            
            node = self._create_node_from_text(
                node_path.strip(),
                cardinality.strip(),
                description.strip(),
                source_url,
                sha256
            )
            if node:
                nodes.append(node)
        
        return nodes
    
    def _extract_nodes_from_table(self, table: List[List[str]], source_url: str, sha256: str) -> List[SpecNode]:
        """Extract nodes from table data."""
        nodes = []
        
        if not table or len(table) < 2:
            return nodes
        
        # Debug: print table structure
        print(f"Table with {len(table)} rows:")
        for i, row in enumerate(table[:3]):  # Show first 3 rows
            if row:  # Check if row is not None
                print(f"  Row {i}: {[cell[:30] + '...' if cell and len(cell) > 30 else cell for cell in row]}")
            else:
                print(f"  Row {i}: [None]")
        
        # Assume first row is header
        headers = [cell.strip() if cell else "" for cell in table[0]]
        
        # Find relevant columns - be more flexible with column detection
        path_col = None
        cardinality_col = None
        description_col = None
        type_col = None
        req_col = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if any(word in header_lower for word in ["xml element", "element", "name"]):
                path_col = i
            elif any(word in header_lower for word in ["req", "required", "mandatory", "optional"]):
                req_col = i
            elif any(word in header_lower for word in ["rep", "repetition", "cardinality", "occurs"]):
                cardinality_col = i
            elif any(word in header_lower for word in ["description", "desc", "comment"]):
                description_col = i
            elif any(word in header_lower for word in ["type", "datatype", "format"]):
                type_col = i
        
        print(f"Detected columns - Path: {path_col}, Req: {req_col}, Cardinality: {cardinality_col}, Description: {description_col}, Type: {type_col}")
        
        # Extract data rows
        for row_idx, row in enumerate(table[1:], 1):
            if not row or len(row) < 2:  # Skip rows with too few columns or None rows
                continue
            
            # Get values with safe indexing
            node_path = row[path_col].strip() if path_col is not None and path_col < len(row) and row[path_col] else ""
            req_value = row[req_col].strip() if req_col is not None and req_col < len(row) and row[req_col] else ""
            cardinality = row[cardinality_col].strip() if cardinality_col is not None and cardinality_col < len(row) and row[cardinality_col] else ""
            description = row[description_col].strip() if description_col is not None and description_col < len(row) and row[description_col] else ""
            data_type = row[type_col].strip() if type_col is not None and type_col < len(row) and row[type_col] else ""
            
            # Skip rows without a proper element name
            if not node_path or len(node_path) < 2:
                continue
            
            # Skip generic "element" entries and XML examples
            if node_path.lower() in ["element", "structure"] or node_path.startswith("<"):
                continue
            
            # Convert cardinality from Norwegian format
            if cardinality in ["0..U", "0..*"]:
                cardinality = "0..*"
            elif cardinality in ["1..U", "1..*"]:
                cardinality = "1..*"
            elif cardinality in ["0..1", "0-1"]:
                cardinality = "0..1"
            elif cardinality in ["1..1", "1-1"]:
                cardinality = "1..1"
            elif not cardinality:
                cardinality = "1..1"  # Default
            
            # Create node
            node = self._create_node_from_text(
                node_path,
                cardinality,
                description,
                source_url,
                sha256,
                data_type
            )
            if node:
                nodes.append(node)
                print(f"  Added node: {node_path} ({cardinality}) - {description[:50]}...")
        
        print(f"Extracted {len(nodes)} nodes from table")
        return nodes
    
    def _create_node_from_text(self, node_path: str, cardinality: str, description: str, 
                              source_url: str, sha256: str, data_type: str = "") -> Optional[SpecNode]:
        """Create a SpecNode from extracted text."""
        if not node_path or len(node_path) < 2:
            return None
        
        # Clean and normalize
        node_path = node_path.strip()
        cardinality = self._normalize_cardinality(cardinality)
        description = description.strip()
        
        if not description:
            description = f"SAF-T element: {node_path}"
        
        # Determine data type if not provided
        if not data_type:
            data_type = self._determine_data_type_from_text(description)
        
        # Extract technical details
        technical_details = self._extract_technical_details(description)
        validation_rules = self._extract_validation_rules(description)
        examples = self._extract_examples(description)
        
        return SpecNode(
            spec="SAF-T",
            version=self.current_version,
            node_path=node_path,
            cardinality=cardinality,
            description=description,
            source_url=source_url,
            sha256=sha256,
            data_type=data_type,
            format=self._determine_format(data_type),
            technical_details=technical_details,
            validation_rules=validation_rules,
            examples=examples,
            publisher="Skatteetaten",
            is_current=True,
            last_updated=datetime.now().isoformat()
        )
    
    def _normalize_cardinality(self, cardinality: str) -> str:
        """Normalize cardinality notation."""
        cardinality = cardinality.strip()
        
        # Handle various formats
        if cardinality in ["1", "1..1", "1-1"]:
            return "1..1"
        elif cardinality in ["0..1", "0-1", "0,1"]:
            return "0..1"
        elif cardinality in ["1..*", "1-*", "1+", "1,*"]:
            return "1..*"
        elif cardinality in ["0..*", "0-*", "0,*", "*"]:
            return "0..*"
        elif ".." in cardinality or "-" in cardinality:
            return cardinality.replace("-", "..")
        else:
            return "1..1"  # Default
    
    def _determine_data_type_from_text(self, text: str) -> str:
        """Determine data type from text description."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["date", "dato", "time", "tid"]):
            return "date"
        elif any(word in text_lower for word in ["amount", "beløp", "sum", "money", "currency"]):
            return "decimal"
        elif any(word in text_lower for word in ["number", "tall", "count", "antall"]):
            return "integer"
        elif any(word in text_lower for word in ["boolean", "true", "false", "yes", "no"]):
            return "boolean"
        elif any(word in text_lower for word in ["complex", "group", "element", "container"]):
            return "complex"
        else:
            return "string"
    
    def _determine_format(self, data_type: str) -> str:
        """Determine format from data type."""
        if data_type == "date":
            return "ISO 8601"
        elif data_type == "decimal":
            return "Decimal"
        elif data_type == "integer":
            return "Integer"
        else:
            return "String"
    
    def _extract_technical_details(self, text: str) -> List[str]:
        """Extract technical details from text."""
        details = []
        
        # Look for length constraints
        length_match = re.search(r'(\d+)\s*(?:characters?|chars?|tegn)', text, re.IGNORECASE)
        if length_match:
            details.append(f"Max length: {length_match.group(1)}")
        
        # Look for pattern constraints
        pattern_match = re.search(r'pattern[:\s]+([^\s,]+)', text, re.IGNORECASE)
        if pattern_match:
            details.append(f"Pattern: {pattern_match.group(1)}")
        
        # Look for format specifications
        format_match = re.search(r'format[:\s]+([^\s,]+)', text, re.IGNORECASE)
        if format_match:
            details.append(f"Format: {format_match.group(1)}")
        
        return details
    
    def _extract_validation_rules(self, text: str) -> List[str]:
        """Extract validation rules from text."""
        rules = []
        
        # Look for validation patterns
        if "required" in text.lower() or "obligatorisk" in text.lower():
            rules.append("Field is required")
        
        if "unique" in text.lower() or "unik" in text.lower():
            rules.append("Value must be unique")
        
        if "not null" in text.lower() or "ikke null" in text.lower():
            rules.append("Value cannot be null")
        
        return rules
    
    def _extract_examples(self, text: str) -> List[str]:
        """Extract examples from text."""
        examples = []
        
        # Look for example patterns
        example_patterns = [
            r'example[:\s]+([^\n,]+)',
            r'eksempel[:\s]+([^\n,]+)',
            r'f\.eks\.\s+([^\n,]+)',
            r'for example[:\s]+([^\n,]+)'
        ]
        
        for pattern in example_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                examples.append(match.strip())
        
        return examples


def parse_saft_pdfs_from_sources(sources: List[Dict[str, str]]) -> List[SpecNode]:
    """Parse SAF-T PDFs from source URLs."""
    parser = SAFTPDFParser()
    all_nodes = []
    
    # PDF URLs from the HTML content
    pdf_urls = {
        "technical_description": "https://www.skatteetaten.no/globalassets/bedrift-og-organisasjon/starte-og-drive/rutiner-regnskap-og-kassasystem/saf-t-regnskap/oppdateringer-mars-2024/norwegian-saf-t-financial-data---technical-description.pdf",
        "header": "https://www.skatteetaten.no/globalassets/bedrift-og-organisasjon/starte-og-drive/rutiner-regnskap-og-kassasystem/saf-t-regnskap/oppdateringer-mars-2024/header.pdf",
        "masterfiles": "https://www.skatteetaten.no/globalassets/bedrift-og-organisasjon/starte-og-drive/rutiner-regnskap-og-kassasystem/saf-t-regnskap/oppdateringer-mars-2024/masterfiles.pdf",
        "generalledger": "https://www.skatteetaten.no/globalassets/bedrift-og-organisasjon/starte-og-drive/rutiner-regnskap-og-kassasystem/saf-t-regnskap/oppdateringer-mars-2024/generalledgerentries.pdf"
    }
    
    for pdf_name, pdf_url in pdf_urls.items():
        print(f"Processing {pdf_name} PDF...")
        
        # Download PDF
        pdf_path = parser.download_pdf(pdf_url, f"saft_{pdf_name}")
        if not pdf_path:
            print(f"Failed to download {pdf_name} PDF")
            continue
        
        # Parse PDF based on type
        if pdf_name == "technical_description":
            nodes = parser.parse_technical_description_pdf(pdf_path, pdf_url, "pdf_hash")
        elif pdf_name == "header":
            nodes = parser.parse_header_pdf(pdf_path, pdf_url, "pdf_hash")
        elif pdf_name == "masterfiles":
            nodes = parser.parse_masterfiles_pdf(pdf_path, pdf_url, "pdf_hash")
        elif pdf_name == "generalledger":
            nodes = parser.parse_generalledger_pdf(pdf_path, pdf_url, "pdf_hash")
        else:
            nodes = parser.parse_technical_description_pdf(pdf_path, pdf_url, "pdf_hash")
        
        print(f"Extracted {len(nodes)} nodes from {pdf_name}")
        all_nodes.extend(nodes)
    
    return all_nodes


def main():
    """Main function to test PDF parsing."""
    # Test with sample sources
    sources = [
        {"source_id": "saft_v1_30", "url": "https://www.skatteetaten.no/en/business-and-organisation/start-and-run/best-practices-accounting-and-cash-register-systems/saf-t-financial/"}
    ]
    
    nodes = parse_saft_pdfs_from_sources(sources)
    
    print(f"\nExtracted {len(nodes)} SAF-T nodes from PDFs")
    
    # Show sample nodes
    for i, node in enumerate(nodes[:5]):
        print(f"\nNode {i+1}:")
        print(f"  Path: {node.node_path}")
        print(f"  Cardinality: {node.cardinality}")
        print(f"  Data Type: {node.data_type}")
        print(f"  Description: {node.description[:100]}...")


if __name__ == "__main__":
    main()
