#!/bin/bash
# Pre-push pipeline validation script
# This script runs the same checks as the GitHub Actions workflows locally

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Track overall status
OVERALL_STATUS=0

# Function to run a check and track status
run_check() {
    local check_name="$1"
    local command="$2"
    
    print_status "Running: $check_name"
    if eval "$command"; then
        print_success "$check_name passed"
    else
        print_error "$check_name failed"
        OVERALL_STATUS=1
    fi
    echo ""
}

print_status "🚀 Starting pre-push pipeline validation..."

# Check if we're in the project directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found. Please run this script from the project root directory."
    exit 1
fi

# Check if uv is available
if ! command -v uv >/dev/null 2>&1; then
    print_error "uv is not installed. Please install it first."
    exit 1
fi

# Install/update dependencies
print_status "Installing dependencies..."
uv sync

echo "=========================================="
print_status "Running Code Quality Checks"
echo "=========================================="

# Ruff check
run_check "Ruff linting" "uv run ruff check . --output-format=github"

# Ruff format check
run_check "Ruff format check" "uv run ruff format --check ."

# MyPy type checking
run_check "MyPy type checking" "uv run mypy modules scripts ingest_from_sources.py --show-error-codes"

echo "=========================================="
print_status "Running Tests"
echo "=========================================="

# Unit tests
run_check "Unit tests" "uv run python -m pytest tests/ -v"

echo "=========================================="
print_status "Running Script Validation"
echo "=========================================="

# Script execution tests
run_check "Script execution test - ingest pipeline" "uv run ingest_from_sources.py --help > /dev/null"
run_check "Script execution test - validate silver" "uv run scripts/validate_silver.py --help > /dev/null"
run_check "Script execution test - export schemas" "uv run scripts/export_json_schemas.py > /dev/null 2>&1"

echo "=========================================="
print_status "Running Seed Data Validation"
echo "=========================================="

# Seed data generation and validation
run_check "Generate and validate seed data" "uv run ingest_from_sources.py seed --with-validation > /dev/null 2>&1"

echo ""

echo "=========================================="
print_status "Final Results"
echo "=========================================="

if [ $OVERALL_STATUS -eq 0 ]; then
    print_success "🎉 All checks passed! Ready to push."
    echo ""
    print_status "Next steps:"
    echo "  git push origin <branch-name>"
    exit 0
else
    print_error "❌ Some checks failed. Please fix the issues before pushing."
    echo ""
    print_status "Quick fixes:"
    echo "  uv run ruff check --fix . && uv run ruff format . && uv run mypy modules scripts ingest_from_sources.py"
    exit 1
fi
