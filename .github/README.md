# GitHub Actions Workflows

This directory contains GitHub Actions workflows for continuous integration and code quality enforcement.

## Workflows

### 1. CI (`ci.yml`)
**Triggers:** Push to main/develop, Pull Requests to main/develop

**Jobs:**
- **test**: Runs tests across Python 3.10, 3.11, 3.12
- **lint-and-format**: Code quality checks (ruff, mypy)
- **data-validation**: Validates Silver layer data
- **security**: Security vulnerability checks
- **build-test**: Package build and installation tests

### 2. PR Validation (`pr-validation.yml`)
**Triggers:** Pull Requests to main/develop

**Checks:**
- Python syntax validation
- Code quality (ruff check, format, mypy)
- Unit tests execution
- Module import tests
- Script execution tests
- TODO/FIXME comment detection
- Debug print statement detection
- Commit message format validation
- File permissions check
- Configuration file validation
- Data validation (if data exists)

### 3. Code Formatting (`format.yml`)
**Triggers:** Manual trigger, Push to main/develop (Python files only)

**Actions:**
- Auto-formats code with ruff
- Auto-fixes linting issues
- Commits and pushes changes automatically

## Branch Protection Setup

To enable branch protection with these workflows:

1. Go to GitHub repository → Settings → Branches
2. Add rule for `main` branch
3. Enable "Require status checks to pass before merging"
4. Select these required status checks:
   - `PR Validation Checks` (from pr-validation.yml)
   - `test` (from ci.yml)
   - `lint-and-format` (from ci.yml)
5. Enable "Require branches to be up to date before merging"
6. Enable "Restrict pushes that create files larger than 100 MB"

## Required Status Checks

The following status checks must pass before merging:

- ✅ **PR Validation Checks** - Comprehensive PR validation
- ✅ **test** - Unit tests across Python versions
- ✅ **lint-and-format** - Code quality and formatting
- ✅ **data-validation** - Data integrity checks
- ✅ **security** - Security vulnerability scanning

## Local Development

Before pushing, run these commands locally:

```bash
# Format code
uv run ruff format .

# Check code quality
uv run ruff check . --fix

# Type checking
uv run mypy modules scripts

# Run tests
uv run python -m pytest tests/ -v
```

## Workflow Status

- 🟢 **Green**: All checks passed
- 🟡 **Yellow**: Workflow in progress
- 🔴 **Red**: Checks failed (fix required before merge)

## Troubleshooting

### Common Issues

1. **Ruff format failures**: Run `uv run ruff format .` locally
2. **Mypy errors**: Fix type annotations or add `# type: ignore` comments
3. **Test failures**: Check test output and fix failing tests
4. **Import errors**: Ensure all modules are properly structured

### Getting Help

If workflows fail:
1. Check the Actions tab for detailed logs
2. Run the same commands locally to reproduce issues
3. Fix issues and push new commits
4. Workflows will re-run automatically
