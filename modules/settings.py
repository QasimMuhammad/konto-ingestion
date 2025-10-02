"""
Configuration management using DynaConf.
Handles settings for local development and Azure deployment.
"""

from dynaconf import Dynaconf
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Initialize DynaConf
settings = Dynaconf(
    settings_files=[
        PROJECT_ROOT / "settings.toml",
    ],
    environments=True,
    envvar_prefix="KONTO",
    load_dotenv=True,
    dotenv_path=PROJECT_ROOT / ".env",
    # Azure Key Vault integration (for future use)
    vault_enabled=False,
    vault_url_from_env="AZURE_KEY_VAULT_URL",
    vault_token_from_env="AZURE_ACCESS_TOKEN",
)


# Validate required settings
def validate_config():
    """Validate that required configuration is present."""
    required_settings = [
        "data_dir",
        "sources_file",
        "http_timeout",
    ]

    missing = []
    for setting in required_settings:
        if not hasattr(settings, setting):
            missing.append(setting)

    if missing:
        raise ValueError(f"Missing required settings: {', '.join(missing)}")

    return True


# Validate on import
validate_config()


# Convenience functions
def get_data_dir() -> Path:
    """Get the data directory path."""
    return PROJECT_ROOT / settings.data_dir


def get_bronze_dir() -> Path:
    """Get the Bronze layer directory path."""
    return PROJECT_ROOT / settings.bronze_dir


def get_silver_dir() -> Path:
    """Get the Silver layer directory path."""
    return PROJECT_ROOT / settings.silver_dir


def get_gold_dir() -> Path:
    """Get the Gold layer directory path."""
    return PROJECT_ROOT / settings.gold_dir


def get_sources_file() -> Path:
    """Get the sources CSV file path."""
    return PROJECT_ROOT / settings.sources_file


def is_azure_mode() -> bool:
    """Check if running in Azure mode."""
    return settings.ENV_FOR_DYNACONF == "production" and bool(
        settings.azure.storage_account_name
    )


def get_azure_config():
    """Get Azure configuration if available."""
    if is_azure_mode():
        return {
            "storage_account_name": settings.azure.storage_account_name,
            "storage_account_key": settings.azure.storage_account_key,
            "key_vault_url": settings.azure.key_vault_url,
            "postgres_connection_string": settings.azure.postgres_connection_string,
        }
    return None
