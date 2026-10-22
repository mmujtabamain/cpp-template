import shutil

from ..common import IS_WINDOWS, CommandRunner, ScaffoldFixture, scaffold


class DevelopmentScriptTests(ScaffoldFixture):
    """Check setup/run diagnostics without downloading dependencies."""

    def test_run_requires_setup(self):
        self.scaffold()
        result = CommandRunner.run(
            ["cmake", "-P", self.project / "scripts/run.cmake"],
            self.project,
            success=False,
        )
        self.assertIn("Run setup.sh / setup.bat first", result.stdout)
        self.assertFalse((self.project / "external").exists())

    def test_existing_bootstrap_failure_preserves_tree(self):
        self.scaffold()
        vcpkg_directory = self.project / "external/vcpkg"
        vcpkg_directory.mkdir(parents=True)
        bootstrap_script = vcpkg_directory / (
            "bootstrap-vcpkg.bat" if IS_WINDOWS else "bootstrap-vcpkg.sh"
        )
        bootstrap_script.write_text(
            "@exit /b 1\n" if IS_WINDOWS else "#!/bin/sh\nexit 1\n"
        )
        result = CommandRunner.run(
            ["cmake", "-P", self.project / "scripts/setup.cmake"],
            self.project,
            success=False,
        )
        self.assertIn("vcpkg bootstrap failed", result.stdout)
        self.assertTrue(bootstrap_script.is_file())
        self.assertIn("setup.sh --clean", result.stdout)
        self.assertIn("Warning:", result.stdout)

    def test_malformed_vcpkg_fails_without_removal(self):
        self.scaffold()
        vcpkg_directory = self.project / "external/vcpkg"
        vcpkg_directory.mkdir(parents=True)
        (vcpkg_directory / "keep").write_text("malformed tree")
        metadata = vcpkg_directory / ".git"
        metadata.mkdir()
        (metadata / "keep").write_text("dependency history")
        result = CommandRunner.run(
            ["cmake", "-P", self.project / "scripts/setup.cmake"],
            self.project,
            success=False,
        )
        self.assertIn("Malformed vcpkg tree", result.stdout)
        self.assertEqual((vcpkg_directory / "keep").read_text(), "malformed tree")
        self.assertEqual((metadata / "keep").read_text(), "dependency history")

    def test_clean_removes_only_generated_setup_state_before_cloning(self):
        self.scaffold()
        for relative in ("external/vcpkg", "vcpkg_installed", "build"):
            directory = self.project / relative
            directory.mkdir(parents=True)
            (directory / "keep").write_text("old state")
        metadata = self.project / ".git"
        metadata.mkdir()
        (metadata / "keep").write_text("project history")
        (self.project / "notes.txt").write_text("user file")
        result = CommandRunner.run(
            [
                "cmake", f"-DGIT_EXECUTABLE={shutil.which('cmake')}",
                "-P", self.project / "scripts/setup.cmake", "--clean",
            ],
            self.project, success=False,
        )
        self.assertIn("Clean setup deletes", result.stdout)
        self.assertIn("vcpkg clone failed", result.stdout)
        for relative in ("external/vcpkg", "vcpkg_installed", "build"):
            self.assertFalse((self.project / relative).exists())
        self.assertEqual((metadata / "keep").read_text(), "project history")
        self.assertEqual((self.project / "notes.txt").read_text(), "user file")
        self.assertTrue((self.project / "src/sample_library.cpp").is_file())
