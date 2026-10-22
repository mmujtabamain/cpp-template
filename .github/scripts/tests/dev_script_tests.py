import os

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
        probe = self.project / ("git-probe.bat" if IS_WINDOWS else "git-probe.sh")
        if IS_WINDOWS:
            probe.write_text(
                "@echo off\n"
                "if defined VCPKG_DEFAULT_BINARY_CACHE exit /b 2\n"
                "(echo %VCPKG_BINARY_SOURCES%&echo %X_VCPKG_ASSET_SOURCES%&echo %VCPKG_DOWNLOADS%)>cache-settings.txt\n"
                "exit /b 1\n"
            )
        else:
            probe.write_text(
                "#!/bin/sh\n"
                'if [ "${VCPKG_DEFAULT_BINARY_CACHE+x}" = x ]; then exit 2; fi\n'
                "printf '%s\\n' \"$VCPKG_BINARY_SOURCES\" \"$X_VCPKG_ASSET_SOURCES\" \"$VCPKG_DOWNLOADS\" > cache-settings.txt\n"
                "exit 1\n"
            )
            probe.chmod(0o755)
        environment = dict(os.environ)
        for name in ("VCPKG_BINARY_SOURCES", "X_VCPKG_ASSET_SOURCES", "VCPKG_DOWNLOADS", "VCPKG_DEFAULT_BINARY_CACHE"):
            environment[name] = "inherited-cache"
        result = CommandRunner.run(
            [
                "cmake", f"-DGIT_EXECUTABLE={probe}",
                "-P", self.project / "scripts/setup.cmake", "--clean",
            ],
            self.project, success=False, environment=environment,
        )
        self.assertEqual(
            (self.project / "cache-settings.txt").read_text().splitlines(),
            ["clear", "clear", (self.project / "external/vcpkg/downloads").as_posix()],
        )
        self.assertIn("Clean setup deletes", result.stdout)
        self.assertIn("vcpkg clone failed", result.stdout)
        for relative in ("external/vcpkg", "vcpkg_installed", "build"):
            self.assertFalse((self.project / relative).exists())
        self.assertEqual((metadata / "keep").read_text(), "project history")
        self.assertEqual((self.project / "notes.txt").read_text(), "user file")
        self.assertTrue((self.project / "src/sample_library.cpp").is_file())

    def test_clean_creates_downloads_before_bootstrapping_fresh_clone(self):
        self.scaffold()
        fixture = self.workspace / "vcpkg source"
        fixture.mkdir()
        (fixture / "bootstrap-vcpkg.sh").write_text(
            '#!/bin/sh\n'
            '[ -d "$VCPKG_DOWNLOADS" ] || exit 42\n'
            'echo ready > "$VCPKG_DOWNLOADS/ready"\n'
            'exit 1\n'
        )
        (fixture / "bootstrap-vcpkg.bat").write_text(
            '@if not exist "%VCPKG_DOWNLOADS%\\" exit /b 42\n'
            '@echo ready>"%VCPKG_DOWNLOADS%\\ready"\n'
            '@exit /b 1\n'
        )
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        CommandRunner.run(["git", "init"], fixture, environment=environment)
        CommandRunner.run(["git", "add", "."], fixture, environment=environment)
        CommandRunner.run(
            ["git", "-c", "user.name=Setup Test", "-c", "user.email=test@example.invalid",
             "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
             "commit", "-m", "Bootstrap fixture"],
            fixture, environment=environment,
        )
        environment.update({
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": f"url.{fixture.as_uri()}.insteadOf",
            "GIT_CONFIG_VALUE_0": "https://github.com/microsoft/vcpkg.git",
            "GIT_CONFIG_KEY_1": "protocol.file.allow",
            "GIT_CONFIG_VALUE_1": "always",
        })
        result = CommandRunner.run(
            ["cmake", "-P", self.project / "scripts/setup.cmake", "--clean"],
            self.project, environment=environment, success=False,
        )
        self.assertIn("vcpkg bootstrap failed", result.stdout)
        self.assertEqual(
            (self.project / "external/vcpkg/downloads/ready").read_text().strip(), "ready",
        )
