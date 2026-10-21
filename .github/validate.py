#!/usr/bin/env python3
"""Validate the C++ template in disposable projects using Python and CMake."""

import argparse
import unittest

from scripts.tests.scaffold_gen_tests import ScaffoldGenerationTests
from scripts.tests.scaffold_safety_tests import ScaffoldSafetyTests
from scripts.tests.scaffold_location_tests import ScaffoldLocationTests
from scripts.tests.scaffold_git_tests import ScaffoldGitTests
from scripts.tests.dev_script_tests import DevelopmentScriptTests
from scripts.tests.hook_tests import GitHookTests
from scripts.tests.integration_tests import IntegrationTests


class ValidationApplication:
    """Select suites; scenario classes own assertions and workspace cleanup."""

    def run(self, *, full=False) -> int:
        test_classes = [
            ScaffoldGenerationTests,
            ScaffoldSafetyTests,
            ScaffoldLocationTests,
            ScaffoldGitTests,
            DevelopmentScriptTests,
            GitHookTests,
        ]
        if full:
            test_classes.append(IntegrationTests)

        suite = unittest.TestSuite(
            unittest.defaultTestLoader.loadTestsFromTestCase(test_class)
            for test_class in test_classes
        )
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1


# MARK: Entry
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full",
        action="store_true",
        help="also download real vcpkg/fmt and build, install, and consume both templates",
    )
    arguments = parser.parse_args()
    return ValidationApplication().run(full=arguments.full)


if __name__ == "__main__":
    raise SystemExit(main())
