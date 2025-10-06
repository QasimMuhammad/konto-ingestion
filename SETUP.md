# Setup Guide

This guide will help you set up the Konto Ingestion project environment quickly and easily.

## Prerequisites

- **Python 3.10 or higher** (already installed on your system)
- Internet connection for downloading dependencies

## Quick Setup

### Linux/macOS

```bash
# Make the setup script executable and run it
chmod +x setup.sh
./setup.sh
```

### Windows

```cmd
# Run the setup batch file
setup.bat
```

## What the Setup Script Does

1. **Verifies Python Version**: Checks that Python 3.10+ is installed
2. **Installs uv**: Downloads and installs the uv package manager if not present
3. **Installs Dependencies**: Uses `uv sync` to install all project dependencies
4. **Verifies Installation**: Tests that core modules and scripts work correctly
5. **Creates Directories**: Sets up the required data directory structure
6. **Provides Guidance**: Shows next steps and available commands

## Manual Setup (Alternative)

If you prefer to set up manually or the automated script fails:

### 1. Install uv

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Create Data Directories

```bash
mkdir -p data/bronze data/silver data/gold
```

### 4. Verify Installation

```bash
# Test core modules
uv run python -c "import modules.logger; print('Setup successful!')"

# Test a script
uv run process-rates-to-silver --help
```

## Post-Setup

After successful setup, you can:

### List Available Sources
```bash
uv run konto-ingest list
```

### Run Ingestion
```bash
# Ingest tax regulations
uv run konto-ingest ingest --domain tax

# Ingest all domains
uv run konto-ingest ingest
```

### Process Data
```bash
# Process VAT rates
uv run process-rates-to-silver

# Validate Silver layer
uv run validate-silver-enhanced
```

## Troubleshooting

### Python Version Issues
- Ensure Python 3.10+ is installed and accessible via `python3` or `python`
- On some systems, you may need to use `python3` instead of `python`

### uv Installation Issues
- On Linux/macOS, ensure curl is installed
- On Windows, ensure PowerShell execution policy allows script execution
- Manual installation: https://github.com/astral-sh/uv

### Permission Issues
- Ensure you have write permissions in the project directory
- On Linux/macOS, you may need to run with `sudo` for system-wide uv installation

### Network Issues
- Ensure you have internet access for downloading dependencies
- Check firewall settings if downloads fail

## Environment Variables

The setup script will configure the environment automatically. If you need to set up manually:

```bash
# Add uv to PATH (Linux/macOS)
export PATH="$HOME/.cargo/bin:$PATH"

# Add uv to PATH (Windows)
set PATH=%USERPROFILE%\.cargo\bin;%PATH%
```

## Verification Commands

After setup, verify everything works:

```bash
# Check Python version
python3 --version  # or python --version

# Check uv version
uv --version

# Test project installation
uv run python -c "import modules.logger, modules.schemas; print('All modules imported successfully')"

# List available scripts
uv run --help
```

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Verify Python and uv versions meet requirements
3. Ensure you're running the setup script from the project root directory
4. Check that all dependencies were installed successfully

## Next Steps

Once setup is complete, see the main [README.md](README.md) for detailed usage instructions and project documentation.
