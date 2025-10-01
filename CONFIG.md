# Configuration Management

This project uses [DynaConf](https://www.dynaconf.com/) for configuration management, supporting both local development and Azure deployment.

## Configuration Files

### `settings.toml`
Main configuration file with default settings and environment-specific overrides.

### `env.example`
Template for environment variables. Copy to `.env` for local development.

## Usage

### Basic Configuration
```python
from modules.config import settings

# Access settings
data_dir = settings.data_dir
http_timeout = settings.http_timeout
log_level = settings.log_level
```

### Environment-Specific Settings
```bash
# Development
ENV_FOR_DYNACONF=development

# Production
ENV_FOR_DYNACONF=production
```

### Azure Integration (Future)
```python
from modules.config import is_azure_mode, get_azure_config

if is_azure_mode():
    azure_config = get_azure_config()
    # Use Azure storage, Key Vault, etc.
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV_FOR_DYNACONF` | Environment (development/production) | development |
| `LOG_LEVEL` | Logging level | INFO |
| `HTTP_TIMEOUT` | HTTP request timeout | 30 |
| `AZURE_STORAGE_ACCOUNT_NAME` | Azure storage account | - |
| `AZURE_KEY_VAULT_URL` | Azure Key Vault URL | - |

## Local Development

1. Copy `env.example` to `.env`
2. Modify settings as needed
3. Run scripts normally

## Azure Deployment (Future)

1. Set environment variables in Azure
2. Configure Azure Key Vault integration
3. Set `ENV_FOR_DYNACONF=production`
