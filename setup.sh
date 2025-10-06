#!/bin/bash
# Konto Ingestion Setup Script
# This script sets up the development environment for the konto-ingestion project

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get Python version
get_python_version() {
    python3 --version 2>/dev/null | cut -d' ' -f2 || echo "not found"
}

# Function to compare versions
version_compare() {
    if [[ $1 == $2 ]]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    # fill empty fields in ver1 with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            # fill empty fields in ver2 with zeros
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1  # ver1 > ver2
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2  # ver1 < ver2
        fi
    done
    return 0  # ver1 == ver2
}

print_status "🚀 Starting Konto Ingestion Setup..."

# Check Python version
print_status "Checking Python version..."
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(get_python_version)
print_status "Found Python version: $PYTHON_VERSION"

# Check if Python version is >= 3.10 (simple check)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -gt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]); then
    print_success "Python version $PYTHON_VERSION is compatible (>= 3.10.0)"
else
    print_error "Python version $PYTHON_VERSION is too old. Please install Python 3.10 or higher."
    exit 1
fi

# Check and install uv
print_status "Checking uv installation..."
if ! command_exists uv; then
    print_status "uv not found. Installing uv..."
    
    # Install uv using the official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Verify installation
    if command_exists uv; then
        print_success "uv installed successfully"
        uv --version
    else
        print_error "Failed to install uv. Please install it manually from https://github.com/astral-sh/uv"
        exit 1
    fi
else
    print_success "uv is already installed"
    uv --version
fi

# Check if we're in the project directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found. Please run this script from the project root directory."
    exit 1
fi

# Install project dependencies
print_status "Installing project dependencies..."
uv sync

# Verify installation
print_status "Verifying installation..."

# Check if key scripts are available
if uv run python -c "import modules.logger; print('Logger module imported successfully')" 2>/dev/null; then
    print_success "Core modules are working correctly"
else
    print_error "Failed to import core modules. Please check the installation."
    exit 1
fi

# Test a simple script
print_status "Testing script execution..."
if uv run process-rates-to-silver --help >/dev/null 2>&1; then
    print_success "Scripts are working correctly"
else
    print_warning "Some scripts might not be working correctly, but core installation is complete"
fi

# Create data directories if they don't exist
print_status "Creating data directories..."
mkdir -p data/bronze data/silver data/gold
print_success "Data directories created"

# Check if sources.csv exists
if [ ! -f "configs/sources.csv" ]; then
    print_warning "configs/sources.csv not found. You may need to create it."
else
    print_success "Configuration files found"
fi

# Display setup completion message
echo ""
print_success "🎉 Setup completed successfully!"
echo ""
print_status "Next steps:"
echo "  1. Verify your configuration in configs/sources.csv"
echo "  2. Run a test ingestion: uv run konto-ingest list"
echo "  3. Start processing: uv run konto-ingest ingest --domain tax"
echo ""
print_status "Available commands:"
echo "  uv run konto-ingest list                    # List available sources"
echo "  uv run konto-ingest ingest --domain tax     # Ingest tax regulations"
echo "  uv run process-rates-to-silver             # Process VAT rates"
echo "  uv run validate-silver                     # Validate Silver layer data"
echo "  uv run validate-silver-enhanced            # Enhanced validation with quality metrics"
echo ""
print_status "For development:"
echo "  uv run --help                              # Show all available commands"
echo "  uv run python -c 'import modules.logger'  # Test Python imports"
echo ""
print_success "Happy coding! 🚀"
