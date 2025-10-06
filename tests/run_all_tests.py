#!/usr/bin/env python3
"""
Run all tests in the test suite.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


def run_tests():
    """Run all tests."""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern="test_*.py")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
