"""Exercise real Git commits and merges against isolated validation hooks."""

import os
from pathlib import Path
import sys
import tempfile
import unittest

from .support import command, fresh

# MARK: Real Git repository fixture


class GitHookTests(unittest.TestCase):
    """Check policy with a tiny validator so hook tests cannot invoke themselves."""

    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory(prefix="cpp-template-hooks-")
        self.addCleanup(temporary_directory.cleanup)
        self.project = fresh(Path(temporary_directory.name), "repository with spaces")
        self.marker = self.project / ".template/validation-marker"
        self.marker.write_text("valid")
        (self.project / ".github/validate.py").write_text(
            "from pathlib import Path\n"
            "raise SystemExit(0 if Path('.template/validation-marker').read_text() == 'valid' else 1)\n"
        )
        # Isolate these repositories from Git's hook-specific index and config.
        self.environment = {
            name: value
            for name, value in os.environ.items()
            if not name.startswith("GIT_")
        }
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Template Validation")
        self.git("config", "user.email", "validation@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        command(
            [sys.executable, self.project / ".github/install-hooks.py"],
            self.project,
            environment=self.environment,
        )
        self.git("add", "--all")
        self.git("commit", "-m", "Create valid fixture")

    def git(self, *arguments, success=True):
        return command(
            ["git", *arguments],
            self.project,
            environment=self.environment,
            success=success,
        )

    def stage_invalid_template(self):
        self.marker.write_text("invalid")
        self.git("add", ".template/validation-marker")

    # MARK: Commit status and index isolation

    def test_valid_commits_on_main_and_feature_branch(self):
        self.git("commit", "--allow-empty", "-m", "Validate main")
        self.git("switch", "-c", "feature")
        self.git("commit", "--allow-empty", "-m", "Validate feature")

    def test_invalid_main_commit_is_blocked(self):
        original_head = self.git("rev-parse", "HEAD").stdout
        self.stage_invalid_template()
        result = self.git("commit", "-m", "Reject invalid template", success=False)
        self.assertIn("commit to main blocked", result.stdout)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, original_head)

    def test_invalid_feature_commit_warns_and_succeeds(self):
        self.git("switch", "-c", "feature")
        self.stage_invalid_template()
        result = self.git("commit", "-m", "Allow work in progress")
        self.assertIn("WARNING", result.stdout)
        self.assertIn("commit allowed", result.stdout)

    def test_staged_failure_cannot_be_hidden_by_working_tree_fix(self):
        self.stage_invalid_template()
        self.marker.write_text("valid")
        self.git("commit", "-m", "Reject staged failure", success=False)
        self.assertEqual(self.marker.read_text(), "valid")
        self.assertEqual(
            self.git("show", ":.template/validation-marker").stdout, "invalid"
        )

    def test_unstaged_failure_does_not_block_valid_commit(self):
        self.marker.write_text("invalid")
        self.git("commit", "--allow-empty", "-m", "Validate index only")
        self.assertEqual(self.marker.read_text(), "invalid")

    def test_commit_only_validates_its_temporary_index(self):
        self.stage_invalid_template()
        readme = self.project / "README.md"
        readme.write_text(readme.read_text() + "\nA documentation update.\n")
        self.git(
            "commit", "--only", "-m", "Commit documentation only", "--", "README.md"
        )
        self.assertEqual(
            self.git("show", "HEAD:.template/validation-marker").stdout, "valid"
        )
        self.assertEqual(
            self.git("show", ":.template/validation-marker").stdout, "invalid"
        )

    def test_missing_staged_validator_blocks_main(self):
        self.git("rm", ".github/validate.py")
        result = self.git("commit", "-m", "Reject missing validator", success=False)
        self.assertIn("staged .github/validate.py is missing", result.stdout)

    def test_generated_project_can_remove_template_sources(self):
        self.git("rm", "-r", ".template")
        (self.project / "CMakeLists.txt").write_text("# Generated project\n")
        self.git("add", "CMakeLists.txt")
        result = self.git("commit", "-m", "Finish project generation")
        self.assertIn("generated-project CI handles builds", result.stdout)

    def test_missing_template_sources_block_unscaffolded_repository(self):
        self.git("rm", "-r", ".template")
        result = self.git("commit", "-m", "Reject missing sources", success=False)
        self.assertIn("Staged template sources are missing", result.stdout)

    def test_installer_preserves_custom_hooks_path(self):
        self.git("config", "core.hooksPath", "custom-hooks")
        command(
            [sys.executable, self.project / ".github/install-hooks.py"],
            self.project,
            environment=self.environment,
            success=False,
        )
        self.assertEqual(
            self.git("config", "--local", "--get", "core.hooksPath").stdout.strip(),
            "custom-hooks",
        )

    # MARK: Automatic merge commits

    def test_invalid_merge_into_main_is_blocked(self):
        self.git("switch", "-c", "feature")
        self.stage_invalid_template()
        self.git("commit", "-m", "Save invalid work in progress")
        self.git("switch", "main")
        original_head = self.git("rev-parse", "HEAD").stdout
        result = self.git(
            "merge", "--no-ff", "feature", "-m", "Reject merge", success=False
        )
        self.assertIn("commit to main blocked", result.stdout)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, original_head)

    def test_invalid_merge_into_feature_branch_warns(self):
        self.git("switch", "-c", "work-in-progress")
        self.stage_invalid_template()
        self.git("commit", "-m", "Save invalid work in progress")
        self.git("switch", "-c", "feature", "main")
        result = self.git(
            "merge", "--no-ff", "work-in-progress", "-m", "Allow feature merge"
        )
        self.assertIn("WARNING", result.stdout)
