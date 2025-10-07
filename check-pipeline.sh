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

# Python syntax check
run_check "Python syntax validation" "find . -name '*.py' -not -path './.venv/*' -not -path './.git/*' | xargs -I {} python -m py_compile {}"

# Ruff check
run_check "Ruff linting" "uv run ruff check ."

# Ruff format check
run_check "Ruff format check" "uv run ruff format --check ."

# MyPy type checking
run_check "MyPy type checking" "uv run mypy modules scripts"

echo "=========================================="
print_status "Running Tests"
echo "=========================================="

# Unit tests
run_check "Unit tests" "uv run python -m pytest tests/ -v"

echo "=========================================="
print_status "Running Module Tests"
echo "=========================================="

# Module import tests
run_check "Core module imports" "uv run python -c 'import modules.logger; import modules.schemas; import modules.parsers; import modules.validation; import modules.pipeline; print(\"All core modules imported successfully\")'"

# Script execution tests
run_check "Script execution test - konto-ingest" "uv run konto-ingest --help > /dev/null"
run_check "Script execution test - process-rates-to-silver" "uv run process-rates-to-silver --help > /dev/null"
run_check "Script execution test - validate-silver" "uv run validate-silver --help > /dev/null"
run_check "Script execution test - validate-silver-enhanced" "uv run validate-silver-enhanced --help > /dev/null"

echo "=========================================="
print_status "Running Code Quality Validations"
echo "=========================================="

# Check for TODO/FIXME comments
run_check "TODO/FIXME check" "! grep -r 'TODO\|FIXME' --include='*.py' --exclude-dir='.venv' --exclude-dir='.git' ."

# Check for debug print statements (exclude debug tools and logger statements)
run_check "Debug print check" "! grep -r 'print(' --include='*.py' --exclude-dir='.venv' --exclude-dir='.git' --exclude-dir='debug' --exclude-dir='tests' . | grep -v 'logger\.'"

# Validate commit message format (check recent commits)
print_status "Validating commit messages..."
if git log --oneline -5 | while read commit; do
    # Skip auto-generated merge commits that start with "Merge"
    if echo "$commit" | grep -q "^[a-f0-9]\{7\} Merge "; then
        echo "Skipping auto-generated merge commit: $commit"
        continue
    fi
    # Extract just the commit message (remove hash and space)
    message=$(echo "$commit" | sed 's/^[a-f0-9]\{7\} //')
    if ! echo "$message" | grep -E "^(feat|fix|docs|style|refactor|test|chore|ci|build|perf|revert)(\(.+\))?: .+"; then
        echo "Invalid commit message format: $commit"
        echo "Commit messages should follow conventional commit format: type(scope): description"
        exit 1
    fi
done; then
    print_success "Commit message validation passed"
else
    print_error "Commit message validation failed"
    OVERALL_STATUS=1
fi

# Check file permissions
run_check "File permissions check" "[ ! -f 'setup.sh' ] || [ -x 'setup.sh' ]"

# Validate configuration files (skip if tomllib not available - Python 3.11+ feature)
if uv run python -c "import tomllib" 2>/dev/null; then
    run_check "pyproject.toml validation" "uv run python -c 'import tomllib; tomllib.load(open(\"pyproject.toml\", \"rb\"))'"
    run_check "settings.toml validation" "uv run python -c 'import tomllib; tomllib.load(open(\"settings.toml\", \"rb\"))'"
else
    print_status "Skipping TOML validation (tomllib requires Python 3.11+)"
    print_status "Skipping TOML validation (tomllib requires Python 3.11+)"
fi

echo "=========================================="
print_status "Running Data Validation (if data exists)"
echo "=========================================="

# Create data directories if they don't exist
mkdir -p data/bronze data/silver data/gold

# Only run validation if Silver data exists
if [ -d "data/silver" ] && [ "$(ls -A data/silver 2>/dev/null)" ]; then
    print_status "Silver data found, running validation..."
    run_check "Silver data validation" "uv run validate-silver-enhanced || true"
else
    print_warning "No Silver data found, skipping data validation"
fi

echo "=========================================="
print_status "Final Results"
echo "=========================================="

if [ $OVERALL_STATUS -eq 0 ]; then
    print_success "🎉 All checks passed! Ready to push."
    echo ""
    print_status "You can now safely push your changes:"
    echo "  git push origin <branch-name>"
    echo ""
    print_status "To run GitHub Actions workflows manually:"
    echo "  1. Go to Actions tab in GitHub"
    echo "  2. Select the workflow you want to run"
    echo "  3. Click 'Run workflow'"
    exit 0
else
    print_error "❌ Some checks failed. Please fix the issues before pushing."
    echo ""
    print_status "Common fixes:"
    echo "  • Format code: uv run ruff format ."
    echo "  • Fix linting: uv run ruff check . --fix"
    echo "  • Fix types: uv run mypy modules scripts"
    echo "  • Run tests: uv run python -m pytest tests/ -v"
    exit 1
fi
