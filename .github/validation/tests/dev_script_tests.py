from ..common import IS_WINDOWS, CommandRunner, ScaffoldFixture, scaffold


class DevelopmentScriptTests(ScaffoldFixture):
    """Check setup/run diagnostics without downloading dependencies."""

    def test_run_requires_setup(self):
        scaffold(self.project)
        result = CommandRunner.run(
            ["cmake", "-P", self.project / "scripts/run.cmake"],
            self.project,
            success=False,
        )
        self.assertIn("Run setup.sh / setup.bat first", result.stdout)
        self.assertFalse((self.project / "external").exists())

    def test_existing_bootstrap_failure_preserves_tree(self):
        scaffold(self.project)
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

    def test_malformed_vcpkg_fails_without_removal(self):
        scaffold(self.project)
        vcpkg_directory = self.project / "external/vcpkg"
        vcpkg_directory.mkdir(parents=True)
        (vcpkg_directory / "keep").write_text("malformed tree")
        result = CommandRunner.run(
            ["cmake", "-P", self.project / "scripts/setup.cmake"],
            self.project,
            success=False,
        )
        self.assertIn("Malformed vcpkg tree", result.stdout)
        self.assertEqual((vcpkg_directory / "keep").read_text(), "malformed tree")
