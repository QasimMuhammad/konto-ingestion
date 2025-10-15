#!/bin/bash
# Quick pre-commit validation script
# Run this before committing to catch issues early

set -e

echo "🔍 Running quick pre-commit checks..."

# Check if uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ uv is not installed. Please install it first."
    exit 1
fi

# Install dependencies if needed
uv sync

# Quick checks
echo "🔧 Fixing linting issues..."
uv run ruff check --fix .

echo "📝 Formatting code..."
uv run ruff format .

echo "🔍 Checking for remaining issues..."
uv run ruff check .

# Validate seed scripts if they were modified
if git diff --cached --name-only | grep -qE "modules/seed/|modules/schemas.py"; then
    echo "🌱 Validating seed data generation..."
    uv run ingest_from_sources.py seed --with-validation
    
    echo "📋 Exporting JSON Schemas..."
    uv run scripts/export_json_schemas.py
fi

echo "✅ All pre-commit checks passed!"
