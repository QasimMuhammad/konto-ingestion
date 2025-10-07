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
echo "📝 Checking code formatting..."
uv run ruff format --check .

echo "🔍 Checking code quality..."
uv run ruff check .

echo "🔧 Checking types..."
uv run mypy modules scripts

echo "🧪 Running tests..."
uv run python -m pytest tests/ -v --tb=short

echo "✅ All pre-commit checks passed!"
