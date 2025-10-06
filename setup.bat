@echo off
REM Konto Ingestion Setup Script for Windows
REM This script sets up the development environment for the konto-ingestion project

setlocal enabledelayedexpansion

echo [INFO] 🚀 Starting Konto Ingestion Setup...

REM Check Python version
echo [INFO] Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Found Python version: %PYTHON_VERSION%

REM Check if Python version is >= 3.10 (basic check)
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)
if %MAJOR% LSS 3 (
    echo [ERROR] Python version %PYTHON_VERSION% is too old. Please install Python 3.10 or higher.
    pause
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 10 (
    echo [ERROR] Python version %PYTHON_VERSION% is too old. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo [SUCCESS] Python version %PYTHON_VERSION% is compatible (>= 3.10.0)

REM Check and install uv
echo [INFO] Checking uv installation...
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] uv not found. Installing uv...
    
    REM Install uv using the official installer
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    REM Add uv to PATH for current session
    set PATH=%USERPROFILE%\.cargo\bin;%PATH%
    
    REM Verify installation
    uv --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install uv. Please install it manually from https://github.com/astral-sh/uv
        pause
        exit /b 1
    )
    
    echo [SUCCESS] uv installed successfully
    uv --version
) else (
    echo [SUCCESS] uv is already installed
    uv --version
)

REM Check if we're in the project directory
if not exist "pyproject.toml" (
    echo [ERROR] pyproject.toml not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Install project dependencies
echo [INFO] Installing project dependencies...
uv sync
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Verify installation
echo [INFO] Verifying installation...

REM Check if key modules are available
uv run python -c "import modules.logger; print('Logger module imported successfully')" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to import core modules. Please check the installation.
    pause
    exit /b 1
)
echo [SUCCESS] Core modules are working correctly

REM Test a simple script
echo [INFO] Testing script execution...
uv run process-rates-to-silver --help >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Some scripts might not be working correctly, but core installation is complete
) else (
    echo [SUCCESS] Scripts are working correctly
)

REM Create data directories if they don't exist
echo [INFO] Creating data directories...
if not exist "data\bronze" mkdir data\bronze
if not exist "data\silver" mkdir data\silver
if not exist "data\gold" mkdir data\gold
echo [SUCCESS] Data directories created

REM Check if sources.csv exists
if not exist "configs\sources.csv" (
    echo [WARNING] configs\sources.csv not found. You may need to create it.
) else (
    echo [SUCCESS] Configuration files found
)

REM Display setup completion message
echo.
echo [SUCCESS] 🎉 Setup completed successfully!
echo.
echo [INFO] Next steps:
echo   1. Verify your configuration in configs\sources.csv
echo   2. Run a test ingestion: uv run konto-ingest list
echo   3. Start processing: uv run konto-ingest ingest --domain tax
echo.
echo [INFO] Available commands:
echo   uv run konto-ingest list                    # List available sources
echo   uv run konto-ingest ingest --domain tax     # Ingest tax regulations
echo   uv run process-rates-to-silver             # Process VAT rates
echo   uv run validate-silver                     # Validate Silver layer data
echo   uv run validate-silver-enhanced            # Enhanced validation with quality metrics
echo.
echo [INFO] For development:
echo   uv run --help                              # Show all available commands
echo   uv run python -c "import modules.logger"  # Test Python imports
echo.
echo [SUCCESS] Happy coding! 🚀
echo.
pause
