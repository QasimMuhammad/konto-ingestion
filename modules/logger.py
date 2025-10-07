"""
Centralized logging configuration using loguru.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from .settings import settings


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
) -> None:
    """
    Setup loguru logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Optional custom format string
    """
    # Remove default handler
    logger.remove()

    # Get configuration from settings
    log_level = level or settings.get("log_level", "INFO")
    log_format = format_string or settings.get(
        "log_format",
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    log_rotation = settings.get("log_rotation", "10 MB")
    log_retention = settings.get("log_retention", "7 days")

    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format=log_format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            level=log_level,
            format=log_format,
            rotation=log_rotation,
            retention=log_retention,
            backtrace=True,
            diagnose=True,
        )

    # Set up trace logging for debug mode
    if log_level == "DEBUG":
        logger.add(
            sys.stderr,
            level="TRACE",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
            filter=lambda record: record["level"].name == "TRACE",
        )


def get_logger(name: str | None = None):
    """
    Get a logger instance.

    Args:
        name: Optional logger name

    Returns:
        Logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger


# Initialize logging on module import
setup_logging()

# Export logger for easy importing
__all__ = ["logger", "setup_logging", "get_logger"]
