from ..common import scaffold, ScaffoldFixture, ProjectWorkspace

class ScaffoldSafetyTests(ScaffoldFixture):
    """Prove cancellation and invalid input preserve existing work."""

    def test_declined_and_confirmed_replacement(self):
        scaffold(self.project)
        (self.project / "src/valuable.cpp").write_text("user modifications")
        original_contents = ProjectWorkspace.snapshot(self.project)
        for answer in ("", "n\n"):
            result = scaffold(self.project, "Replacement", "exec", answer=answer)
            self.assertIn("cancelled", result.stdout)
            self.assertEqual(original_contents, ProjectWorkspace.snapshot(self.project))
        for path in (".git/keep", "external/vcpkg/keep", ".github/keep", "notes.txt"):
            project = self.project / path
            project.parent.mkdir(parents=True, exist_ok=True)
            project.write_text("preserve")
        (self.project / "build").mkdir()
        (self.project / "vcpkg_installed").mkdir()
        result = scaffold(self.project, "Replacement", "exec", answer="y\n")
        self.assertIn("permanently erase", result.stdout)
        for path in (
            "include",
            "tests",
            "examples",
            "cmake",
            "src/valuable.cpp",
            "build",
            "vcpkg_installed",
        ):
            self.assertFalse((self.project / path).exists(), path)
        for path in (
            ".git/keep",
            "external/vcpkg/keep",
            ".github/keep",
            "notes.txt",
            ".template",
            "scaffold.sh",
            "scaffold.bat",
        ):
            self.assertTrue((self.project / path).exists(), path)
        self.assertIn("Replacement", (self.project / "src/main.cpp").read_text())

    def test_invalid_input_preserves_existing_data(self):
        scaffold(self.project)
        original_contents = ProjectWorkspace.snapshot(self.project)
        for name in ("", "123", "../escape", "bad;name", 'bad"name', "class", "Run"):
            scaffold(self.project, name, force=True, success=False)
            self.assertEqual(original_contents, ProjectWorkspace.snapshot(self.project))
        scaffold(self.project, project_type="invalid", force=True, success=False)
        self.assertEqual(original_contents, ProjectWorkspace.snapshot(self.project))

    def test_partial_output_and_stale_stage_recovery(self):
        (self.project / "src").mkdir()
        (self.project / "src/partial.cpp").write_text("partial")
        staging_directory = self.project / ".template/.scaffold-tmp"
        staging_directory.mkdir()
        (staging_directory / "stale").write_text("stale")
        scaffold(self.project, force=True)
        self.assertFalse((self.project / "src/partial.cpp").exists())
        self.assertTrue((self.project / "tests/sample_library_test.cpp").exists())
        self.assertFalse(staging_directory.exists())

    def test_render_error_preserves_existing_data(self):
        scaffold(self.project)
        (self.project / ".template/templates/common/vcpkg.json.in").write_text(
            "{ broken json"
        )
        original_source = (self.project / "src/sample_library.cpp").read_bytes()
        scaffold(self.project, force=True, success=False)
        self.assertEqual(
            original_source, (self.project / "src/sample_library.cpp").read_bytes()
        )

    def test_missing_source_template_preserves_existing_data(self):
        scaffold(self.project)
        (self.project / ".template/templates/executable/src/main.cpp.in").unlink()
        original_source = (self.project / "src/sample_library.cpp").read_bytes()
        result = scaffold(self.project, project_type="exec", force=True, success=False)
        self.assertIn("missing src/main.cpp", result.stdout)
        self.assertEqual(
            original_source, (self.project / "src/sample_library.cpp").read_bytes()
        )
