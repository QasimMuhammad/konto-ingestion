# Konto Ingestion

A comprehensive data ingestion pipeline for Norwegian legal and regulatory texts, designed to normalize authoritative sources into structured data and generate training datasets for LoRA fine-tuning.

## Goals

- Ingest **authoritative legal/regulatory texts** (Lovdata, Skatteetaten, Altinn)
- Normalize them into structured tables (`law`, `law_section`, `rate_table`, `spec_node`)
- Generate **gold JSONL** datasets ready for LoRA fine-tuning (glossary + synthetic chats)
- Provide a clean, extensible ingestion pipeline that grows with new data sources (e.g., bank feeds, invoices)

## Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation


1. Install dependencies using uv:
   ```bash
   uv sync
   ```

### Development Setup

1. Run code quality checks:
   ```bash
   uv run ruff check --fix . && uv run ruff format . && uv run mypy src scripts && uv run ruff check .
   ```

## Usage

### Main Pipeline

The main entry point provides domain-based ingestion and crawl scheduling:

```bash
# Run ingestion for all domains
uv run main.py ingest

# Run ingestion for specific domain
uv run main.py ingest --domain tax
uv run main.py ingest --domain accounting
uv run main.py ingest --domain reporting

# Run ingestion by crawl frequency
uv run main.py ingest --freq monthly
uv run main.py ingest --freq quarterly
uv run main.py ingest --freq onchange

# List available sources
uv run main.py list
uv run main.py list --domain tax
uv run main.py list --freq monthly
```

### Data Pipeline

The pipeline follows a three-tier architecture:

1. **Bronze Layer**: Raw data ingestion from various sources
2. **Silver Layer**: Cleaned and normalized data
3. **Gold Layer**: Processed datasets ready for training

### Individual Scripts

Run specific ingestion scripts directly:

```bash
# Tax regulations
uv run scripts/ingest_tax_regs.py

# Accounting regulations
uv run scripts/ingest_accounting_regs.py

# Reporting regulations
uv run scripts/ingest_reporting_regs.py

# Process bronze to silver
uv run scripts/process_bronze_to_silver.py
```

### Debug Tools

Explore and visualize processed data:

```bash
# Show summary statistics
uv run debug/visualize_silver.py --summary

# Show sample sections
uv run debug/visualize_silver.py --sample 5

# Filter by domain
uv run debug/visualize_silver.py --sample 3 --domain tax

# Search for specific text
uv run debug/visualize_silver.py --search "merverdiavgift"

# Generate interactive HTML report
uv run debug/generate_html_report.py

# Run all visualization tools
uv run debug/test_visualization.py
```

For detailed debug instructions, see [debug/README.md](debug/README.md).

## Project Structure

```
konto-ingestion/
├── data/
│   ├── bronze/          # Raw ingested data (HTML files)
│   ├── silver/          # Cleaned and normalized data (JSON)
│   └── gold/            # Training-ready datasets (JSONL)
├── modules/             # Core processing modules
│   ├── cleaners/        # Text cleaning and normalization
│   ├── parsers/         # HTML/XML parsers for different sources
│   ├── exporters/       # JSONL export utilities
│   └── utils.py         # Common utilities
├── scripts/             # Ingestion and processing scripts
├── debug/               # Debug utilities and documentation
│   └── README.md        # [Debug Guide](debug/README.md)
├── docs/                # Project documentation
│   └── planning.md      # [Development Planning](docs/planning.md)
├── configs/             # Configuration files
│   └── sources.csv      # Data source definitions
├── tests/               # Test suite
├── main.py              # Main entry point
├── settings.toml        # Application settings
└── pyproject.toml       # Project configuration
```

## Available Features

### Data Ingestion
- **Automated Collection**: Fetches data from Norwegian legal sources
- **Idempotent Processing**: Only downloads changed content
- **Multi-source Support**: Lovdata, Skatteetaten, Altinn
- **Domain Organization**: Tax, accounting, and reporting regulations

### Data Processing
- **Text Normalization**: Cleans and standardizes legal text
- **Section Extraction**: Parses legal documents into structured sections
- **Metadata Enrichment**: Adds provenance and quality information
- **Validation**: Ensures data integrity with Pydantic schemas

### Export Capabilities
- **JSONL Generation**: Creates training-ready datasets
- **Glossary Creation**: Builds domain-specific glossaries
- **Quality Reports**: Generates processing statistics
- **Interactive Reports**: HTML visualization tools

### Debug & Analysis
- **Data Visualization**: Interactive exploration tools
- **Search Functionality**: Find specific content across datasets
- **Quality Analysis**: Assess processing completeness
- **Sample Export**: Extract subsets for inspection

## Development Status

This project is actively developed with the following components implemented:

✅ **Bronze Layer**: Raw data ingestion with SHA256 tracking  
✅ **Silver Layer**: Complete data processing and normalization  
✅ **Parsers**: Lovdata HTML, SAF-T PDF, VAT rates, and A-meldingen parsers  
✅ **Data Validation**: Comprehensive Pydantic schemas with 100% validation success  
✅ **Debug Tools**: Comprehensive data exploration utilities  
✅ **Quality Reports**: Processing statistics and validation  

### Current Data Assets

- **Legal Sections**: 1,804 sections from tax, accounting, and law documents
- **SAF-T Nodes**: 142 technical specification elements with validation rules
- **VAT Rates**: 4 detailed rate entries with categories and validity periods
- **A-meldingen Rules**: 50 comprehensive business rules for monthly reporting
- **Total Records**: 2,514+ validated records across all domains

### Planned Features

🔄 **Gold Layer**: Training dataset generation (Week 3-4)  
🔄 **Rules Engine**: Deterministic compliance rules (Week 3-4)  
🔄 **LoRA Training**: Model fine-tuning pipeline (Week 3-4)  
🔄 **API Service**: REST endpoints for data access  

For detailed development plans, see [docs/planning.md](docs/planning.md).

## Configuration

The pipeline uses several configuration files:

- **`configs/sources.csv`**: Data source definitions and metadata
- **`settings.toml`**: Application settings and parameters
- **`env.example`**: Environment variable template

## Contributing

1. Follow the code quality standards (mypy, ruff)
2. Use type hints for all functions
3. Keep functions focused and composable
4. Run quality checks before committing
5. Add tests for new functionality

## License

[Add your license information here]