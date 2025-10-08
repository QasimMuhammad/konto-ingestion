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

The pipeline runs in two stages: **Bronze ingestion** (sources → bronze) and **Silver processing** (bronze → silver).

```bash
# Run full pipeline: sources → bronze → silver (default)
uv run konto-ingest ingest

# Run for specific domain only
uv run konto-ingest ingest --domain tax
uv run konto-ingest ingest --domain accounting
uv run konto-ingest ingest --domain reporting

# Run bronze ingestion only (skip silver processing)
uv run konto-ingest ingest --bronze-only

# Combine options: domain-specific bronze-only
uv run konto-ingest ingest --domain tax --bronze-only

# List available sources
uv run konto-ingest list
uv run konto-ingest list --domain tax
```

### Data Validation
```bash
# Validate Silver layer data quality
uv run validate-silver

# Save quality report to file
uv run validate-silver --output quality_report.json
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