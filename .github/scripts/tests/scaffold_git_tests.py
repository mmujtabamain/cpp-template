import os

from ..common import (
    CommandRunner,
    ProjectWorkspace,
    ScaffoldFixture,
    launcher,
    scaffold,
)


# MARK: Scaffold Git Tests
class ScaffoldGitTests(ScaffoldFixture):
    def create_metadata(self, project):
        metadata = project / ".git"
        metadata.mkdir()
        (metadata / "keep").write_text("existing history")
        return metadata

    def assert_git_files(self, project, enabled):
        for filename in (".github", ".gitignore", ".gitattributes"):
            self.assertEqual((project / filename).exists(), enabled, filename)
        self.assertFalse((project / ".github/hooks").exists())
        self.assertFalse((project / ".github/validate.py").exists())

    def test_only_template_git_files_remain(self):
        for filename in (
            ".github/old.yml",
            ".githooks/old",
            ".gitmodules",
            ".gitconfig",
        ):
            path = self.project / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("old Git data")

        self.scaffold()
        self.assert_git_files(self.project, True)
        github_files = {
            str(path.relative_to(self.project / ".github")).replace(os.sep, "/")
            for path in (self.project / ".github").rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            github_files, {"workflows/validate.yml", "rulesets/protect-main.json"}
        )
        for filename in (".githooks", ".gitmodules", ".gitconfig"):
            self.assertFalse((self.project / filename).exists())

    def test_native_launcher_disables_git_files(self):
        launcher(self.project, "scaffold", "SampleRuntime", "exec", "--no-git")
        self.assert_git_files(self.project, False)
        self.assertIn(
            "Git files were disabled", (self.project / "README.md").read_text()
        )
        self.assertTrue((self.project / ".scaffold/templates/git/.github").is_dir())

    def test_git_files_can_be_enabled_again(self):
        self.scaffold(git=False)
        self.scaffold(git=True, force=True)
        self.assert_git_files(self.project, True)
        self.assertIn("git init -b main", (self.project / "README.md").read_text())

    def test_git_removal_prompt_defaults_to_keep(self):
        metadata = self.create_metadata(self.project)
        result = self.scaffold(remove_git="ASK")
        self.assertIn("Remove Git metadata? [y/N]", result.stdout)
        self.assertEqual((metadata / "keep").read_text(), "existing history")
        self.assertIn("git remote -v", result.stdout)

    def test_force_does_not_approve_git_removal(self):
        metadata = self.create_metadata(self.project)
        result = self.scaffold(remove_git="ASK", force=True, answer="n\n")
        self.assertIn("Remove Git metadata? [y/N]", result.stdout)
        self.assertTrue(metadata.is_dir())

    def test_confirmed_git_removal_only_affects_the_destination(self):
        source_metadata = self.create_metadata(self.project)
        destination = self.workspace / "generated project"
        destination.mkdir()
        destination_metadata = self.create_metadata(destination)
        result = scaffold(
            self.project,
            "SampleRuntime",
            "exec",
            destination=destination,
            remove_git="ASK",
            answer="y\n",
        )
        self.assertFalse(destination_metadata.exists())
        self.assertEqual((source_metadata / "keep").read_text(), "existing history")
        self.assert_git_files(destination, True)
        self.assertIn("git init -b main", result.stdout)
        self.assertIn("git remote add origin", result.stdout)

    def test_native_history_flags_are_independent_of_git_files(self):
        for history_flag, keep_metadata in (
            ("--keep-git", True),
            ("--remove-git", False),
        ):
            with self.subTest(history_flag=history_flag):
                project = ProjectWorkspace().create(self.workspace, history_flag)
                metadata = self.create_metadata(project)
                result = launcher(
                    project,
                    "scaffold",
                    "SampleRuntime",
                    "exec",
                    "--no-git",
                    history_flag,
                )
                self.assertNotIn("Remove Git metadata? [y/N]", result.stdout)
                self.assertEqual(metadata.exists(), keep_metadata)
                self.assert_git_files(project, False)

    def test_missing_git_template_preserves_existing_project(self):
        self.scaffold()
        original_source = (self.project / "src/sample_library.cpp").read_bytes()
        (self.project / ".scaffold/templates/git/.gitignore").unlink()
        result = self.scaffold(force=True, success=False)
        self.assertIn("missing .gitignore", result.stdout)
        self.assertEqual(
            (self.project / "src/sample_library.cpp").read_bytes(), original_source
        )

    def test_existing_history_and_custom_hooks_are_preserved(self):
        environment = {
            name: value
            for name, value in os.environ.items()
            if not name.startswith("GIT_")
        }
        for hooks_path in (".github/hooks", "custom-hooks"):
            project = ProjectWorkspace().create(
                self.workspace, hooks_path.replace("/", "-")
            )

            def git(*arguments, success=True):
                return CommandRunner.run(
                    ["git", *arguments],
                    project,
                    environment=environment,
                    success=success,
                )

            git("init", "-b", "main")
            git("config", "user.name", "Scaffold Test")
            git("config", "user.email", "test@example.invalid")
            git("add", "README.md")
            git(
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                "Existing history",
            )
            original_head = git("rev-parse", "HEAD").stdout
            git("config", "core.hooksPath", hooks_path)
            git("remote", "add", "origin", "https://example.invalid/template")

            scaffold(project, "SampleRuntime", "exec", remove_git="OFF")
            self.assertEqual(git("rev-parse", "HEAD").stdout, original_head)
            self.assertEqual(
                git("remote", "get-url", "origin").stdout.strip(),
                "https://example.invalid/template",
            )
            result = git(
                "config",
                "--local",
                "--get",
                "core.hooksPath",
                success=hooks_path != ".github/hooks",
            )
            if hooks_path == "custom-hooks":
                self.assertEqual(result.stdout.strip(), hooks_path)

    def test_worktree_pointer_does_not_remove_shared_history(self):
        shared_history = self.workspace / "shared history"
        shared_history.mkdir()
        (shared_history / "keep").write_text("shared history")
        (self.project / ".git").write_text(f"gitdir: {shared_history.as_posix()}\n")
        self.scaffold(remove_git="ON")
        self.assertFalse((self.project / ".git").exists())
        self.assertEqual((shared_history / "keep").read_text(), "shared history")
