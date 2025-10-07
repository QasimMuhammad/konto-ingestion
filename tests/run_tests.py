#!/usr/bin/env python3
"""
Test runner for Silver processing tests.
"""

import sys
import unittest
from pathlib import Path


def run_tests():
    """Run all tests."""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
