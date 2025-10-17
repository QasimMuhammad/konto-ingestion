# Konto Ingestion

A data ingestion pipeline for Norwegian legal and regulatory texts.

## Setup

### Prerequisites
- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Quick Setup

Run the automated setup script:

```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

If you prefer manual setup:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

## Local Pipeline Check

**Always run the local pipeline check before pushing:**

```bash
./check-pipeline.sh
```

This comprehensive validation includes:
- Code quality checks (ruff, mypy)
- Unit tests
- Script execution tests
- Data validation
- Commit message format validation
- Debug print statement checks

## Usage

### Unified Ingestion Pipeline

The pipeline supports multiple stages: **Seed** (static data), **Bronze ingestion** (sources → bronze), and **Silver processing** (bronze → silver).

```bash
# Seed static data (Chart of Accounts + Business Rules)
uv run ingest_from_sources.py seed

# Run full pipeline: sources → bronze → silver
uv run ingest_from_sources.py ingest

# Complete pipeline: seed + ingest
uv run ingest_from_sources.py all

# With validation
uv run ingest_from_sources.py seed --with-validation
uv run ingest_from_sources.py all --with-validation

# Domain-specific ingestion
uv run ingest_from_sources.py ingest --domain tax
uv run ingest_from_sources.py ingest --domain accounting
uv run ingest_from_sources.py ingest --domain reporting

# Bronze only (skip silver processing)
uv run ingest_from_sources.py ingest --bronze-only

# List available sources
uv run ingest_from_sources.py list
uv run ingest_from_sources.py list --domain tax
```

### Data Validation
```bash
# Validate seed data (Chart of Accounts + Business Rules)
uv run ingest_from_sources.py seed --with-validation

# Validate Silver layer data quality
uv run scripts/validate_silver.py

# Export JSON Schemas from Pydantic models
uv run scripts/export_json_schemas.py
```

### Gold Layer Training Data Export
```bash
# Export ALL training data (glossaries + rules + conversations)
uv run export_gold_data.py all

# Export all with custom parameters
uv run export_gold_data.py all --variations-per-rule 20 --conversations-per-template 300

# Export individual datasets:
uv run export_gold_data.py glossary                    # Tax + accounting glossaries
uv run export_gold_data.py glossary --export-type tax  # Tax only
uv run export_gold_data.py rules                       # Rule-based posting proposals
uv run export_gold_data.py synthetic                   # Synthetic conversations

# Validate generated JSONL samples
uv run export_gold_data.py validate

# Run evaluation harness
uv run export_gold_data.py eval --model_name <model_path> --output results/eval_report.json
uv run export_gold_data.py eval --use_expected  # Test harness with perfect scores
```

### Debug Tools
```bash
# Show summary statistics
uv run debug/visualize_silver.py --summary

# Generate interactive HTML report
uv run debug/generate_html_report.py

# Open visualization files
open debug/silver_report.html    # Silver data visualization
open debug/report.html          # General data report
```