# Debug Tools for Silver Layer Data

This directory contains tools for visualizing and inspecting the processed Silver layer data.

## Tools

### 1. `visualize_silver.py` - Command-line Data Inspector

A comprehensive tool for exploring Silver layer data with various analysis options.

**Usage:**
```bash
# Show summary statistics
uv run debug/visualize_silver.py --summary

# Show sample sections
uv run debug/visualize_silver.py --sample 5

# Filter by domain
uv run debug/visualize_silver.py --sample 3 --domain tax

# Run all analyses
uv run debug/visualize_silver.py --all

# Search for specific text
uv run debug/visualize_silver.py --search "merverdiavgift"

# Export sample data
uv run debug/visualize_silver.py --export debug/sample.json
```

**Features:**
- 📊 Summary statistics (domains, source types, publishers, tokens)
- 📋 Sample section display with full metadata
- 📝 Text analysis (word frequency, patterns, length stats)
- 🔍 Search functionality across sections
- 📁 Export sample data to smaller JSON files
- 🔍 Metadata quality analysis

### 2. `generate_html_report.py` - Interactive HTML Report

Generates a beautiful, interactive HTML report for web-based exploration.

**Usage:**
```bash
# Generate HTML report
uv run debug/generate_html_report.py

# Custom input/output files
uv run debug/generate_html_report.py --input data/silver/law_sections.json --output debug/report.html

# Include more sections in sample
uv run debug/generate_html_report.py --sample-size 200
```

**Features:**
- 📈 Interactive charts and visualizations
- 🔍 Searchable section browser
- 📊 Domain/source type/publisher breakdowns
- 🎨 Modern, responsive design
- 📱 Mobile-friendly interface

### 3. `analyze_silver_data.py` - Comprehensive Data Analysis

Advanced analysis tool for all Silver layer data types with schema validation.

**Usage:**
```bash
# Basic analysis
uv run debug/analyze_silver_data.py

# Detailed analysis with schema validation
uv run debug/analyze_silver_data.py --detailed --validate

# Export analysis results
uv run debug/analyze_silver_data.py --export debug/analysis_report.json
```

**Features:**
- 📊 Comprehensive statistics for all data types
- 🔍 Schema validation with detailed error reporting
- 📈 Data quality metrics and completeness analysis
- 📋 Top categories and distribution analysis
- 💾 Export analysis results to JSON

### 4. `test_visualization.py` - Test All Tools

Runs all visualization tools to ensure they work correctly.

**Usage:**
```bash
uv run debug/test_visualization.py
```

## Generated Files

After running the tools, you'll find:

- `debug/sample_sections.json` - Small sample of sections for inspection
- `debug/silver_report.html` - Interactive HTML report (open in browser)
- `debug/quality_report.json` - Processing quality statistics
- `debug/analysis_report.json` - Comprehensive analysis results (if exported)

## Examples

### Quick Data Overview
```bash
uv run debug/visualize_silver.py --summary --text-analysis --quality
```

### Find Specific Content
```bash
uv run debug/visualize_silver.py --search "skatteloven" --sample 10
```

### Generate Web Report
```bash
uv run debug/generate_html_report.py --sample-size 100
open debug/silver_report.html
```

## Data Structure

The Silver layer data contains these key fields:

- **Basic Info**: `law_id`, `section_id`, `path`, `heading`
- **Content**: `text_plain` (cleaned), `text_html` (raw), `token_count`
- **Metadata**: `domain`, `source_type`, `publisher`, `version`
- **Legal**: `law_title`, `chapter`, `repealed`, `amended_dates`
- **Provenance**: `source_url`, `sha256`, `ingested_at`, `processed_at`
- **Quality**: Various validation and processing metrics

## Troubleshooting

If you get errors about missing files:
1. Ensure Silver processing has been run: `uv run process-to-silver`
2. Check that `data/silver/law_sections.json` exists
3. Verify the file is not empty or corrupted

For large files, the tools automatically sample data for performance while still providing comprehensive analysis.
