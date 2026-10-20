#!/usr/bin/env python3
"""Validate the C++ template in disposable projects using Python and CMake."""

import argparse
import unittest

from validation.integration_tests import IntegrationTests
from validation.scaffold_tests import (
    DevelopmentScriptTests,
    ScaffoldGenerationTests,
    ScaffoldSafetyTests,
)

# MARK: Suite composition


class ValidationApplication:
    """Select suites; scenario classes own assertions and workspace cleanup."""

    def run(self, *, integration=False):
        test_classes = [
            ScaffoldGenerationTests,
            ScaffoldSafetyTests,
            DevelopmentScriptTests,
        ]
        if integration:
            test_classes.append(IntegrationTests)

        suite = unittest.TestSuite(
            unittest.defaultTestLoader.loadTestsFromTestCase(test_class)
            for test_class in test_classes
        )
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1


# MARK: Command line entry point


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--integration",
        action="store_true",
        help="also download real vcpkg/fmt and build, install, and consume both templates",
    )
    arguments = parser.parse_args()
    return ValidationApplication().run(integration=arguments.integration)


if __name__ == "__main__":
    raise SystemExit(main())
