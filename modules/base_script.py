#!/usr/bin/env python3
"""
Base script infrastructure for konto-ingestion.
Eliminates code duplication across all processing scripts.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import sys
from typing import Dict, Any, Type
from datetime import datetime
from loguru import logger

# Script registry for auto-discovery
_script_registry: Dict[str, Type["BaseScript"]] = {}


def register_script(script_id: str):
    """Decorator to register a script class with the registry."""

    def decorator(cls: Type[BaseScript]) -> Type[BaseScript]:
        _script_registry[script_id] = cls
        return cls

    return decorator


def get_registered_scripts() -> Dict[str, Type["BaseScript"]]:
    """Get all registered scripts."""
    return _script_registry.copy()


class BaseScript(ABC):
    """Base class for all processing scripts."""

    def __init__(self, script_name: str):
        self.script_name = script_name
        self.setup_path()
        self.setup_logging()
        self.start_time = datetime.now()

    def setup_path(self):
        """Setup path handling - no longer needed with proper package structure."""
        # With proper pyproject.toml configuration, sys.path manipulation is not needed
        # The package structure is handled by the build system
        pass

    def setup_logging(self):
        """Configure logging for the script."""
        # Use loguru logger with script name context
        self.log = logger.bind(script=self.script_name)

    @abstractmethod
    def _execute(self) -> int:
        """
        Execute the script logic.

        Returns:
            0 for success, 1 for failure
        """
        pass

    def main(self) -> int:
        """Main entry point with error handling and timing."""
        try:
            self.log.info(f"Starting {self.script_name}")
            result = self._execute()

            duration = datetime.now() - self.start_time
            self.log.info(
                f"Completed {self.script_name} in {duration.total_seconds():.2f}s with result: {result}"
            )
            return result

        except KeyboardInterrupt:
            self.log.warning(f"Script {self.script_name} interrupted by user")
            return 1
        except Exception as e:
            self.log.error(f"Script {self.script_name} failed: {e}", exc_info=True)
            return 1

    def get_script_info(self) -> Dict[str, Any]:
        """Get script metadata."""
        return {
            "name": self.script_name,
            "start_time": self.start_time.isoformat(),
            "python_version": sys.version,
            "project_root": str(Path(__file__).parent.parent),
        }
