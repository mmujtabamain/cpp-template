import os

from ..common import (
    CommandRunner,
    IS_WINDOWS,
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

    def test_existing_git_files_are_preserved(self):
        files = (
            ".github/old.yml",
            ".github/hooks/pre-commit",
            ".githooks/old",
            ".gitmodules",
            ".gitconfig",
        )
        for filename in files:
            path = self.project / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("existing Git data")

        self.scaffold()
        for filename in files:
            self.assertEqual(
                (self.project / filename).read_text(), "existing Git data"
            )
        self.assertTrue((self.project / ".github/workflows/validate.yml").is_file())
        self.assertTrue((self.project / ".github/rulesets/protect-main.json").is_file())

    def test_native_launcher_disables_git_file_copying(self):
        original_git_files = {
            filename: (self.project / filename).read_bytes()
            for filename in (".gitignore", ".gitattributes", ".github/validate.py")
        }
        launcher(self.project, "scaffold", "SampleRuntime", "exec", "--no-git")
        for filename, original in original_git_files.items():
            self.assertEqual((self.project / filename).read_bytes(), original)
        self.assertIn(
            "Git files were disabled", (self.project / "README.md").read_text()
        )
        self.assertFalse((self.project / "assets/.gitkeep").exists())
        self.assertTrue((self.project / ".scaffold/templates/git/.github").is_dir())

    def test_external_destination_git_files_are_optional(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                destination = self.workspace / str(enabled)
                scaffold(
                    self.project, "SampleRuntime", "exec",
                    destination=destination, git=enabled,
                )
                self.assert_git_files(destination, enabled)
                self.assertEqual((destination / "assets/.gitkeep").exists(), enabled)

    def test_no_git_preserves_previously_generated_git_files(self):
        destination = self.workspace / "generated"
        scaffold(self.project, "SampleRuntime", "exec", destination=destination)
        git_files = {
            path.relative_to(destination): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file() and path.relative_to(destination).parts[0].startswith(".git")
        }
        scaffold(
            self.project, "SampleRuntime", "exec",
            destination=destination, git=False, force=True,
        )
        for filename, original in git_files.items():
            self.assertEqual((destination / filename).read_bytes(), original)

    def test_git_metadata_is_preserved_without_prompting(self):
        metadata = self.create_metadata(self.project)
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                result = self.scaffold(git=enabled, force=True, answer="y\n")
                self.assertNotIn("Remove Git", result.stdout)
                self.assertEqual((metadata / "keep").read_text(), "existing history")

    def test_obsolete_git_flags_are_rejected(self):
        metadata = self.create_metadata(self.project)
        original = ProjectWorkspace.snapshot(self.project)
        script = self.project / (
            "scaffold-here.bat" if IS_WINDOWS else "scaffold-here.sh"
        )
        invocation = ["cmd", "/c", script] if IS_WINDOWS else [script]
        for flag in ("--git", "--keep-git", "--remove-git"):
            with self.subTest(flag=flag):
                result = CommandRunner.run(
                    [*invocation, "SampleRuntime", "exec", flag],
                    self.project, success=False,
                )
                self.assertIn("Unknown scaffold option", result.stdout)
                self.assertEqual(ProjectWorkspace.snapshot(self.project), original)
                self.assertTrue(metadata.is_dir())

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

            scaffold(project, "SampleRuntime", "exec")
            self.assertEqual(git("rev-parse", "HEAD").stdout, original_head)
            self.assertEqual(
                git("remote", "get-url", "origin").stdout.strip(),
                "https://example.invalid/template",
            )
            self.assertEqual(
                git("config", "--local", "--get", "core.hooksPath").stdout.strip(),
                hooks_path,
            )

    def test_worktree_pointer_does_not_remove_shared_history(self):
        shared_history = self.workspace / "shared history"
        shared_history.mkdir()
        (shared_history / "keep").write_text("shared history")
        (self.project / ".git").write_text(f"gitdir: {shared_history.as_posix()}\n")
        self.scaffold()
        self.assertEqual(
            (self.project / ".git").read_text(),
            f"gitdir: {shared_history.as_posix()}\n",
        )
        self.assertEqual((shared_history / "keep").read_text(), "shared history")
