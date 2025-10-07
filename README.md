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

### Main Pipeline
```bash
# Run ingestion for all domains
uv run main.py ingest

# Run ingestion for specific domain
uv run main.py ingest --domain tax

# List available sources
uv run main.py list
```

### Individual Scripts
```bash
# Process bronze to silver
uv run scripts/process_bronze_to_silver.py

# Validate silver data
uv run validate-silver
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