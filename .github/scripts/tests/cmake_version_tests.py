"""Verify selected CMake requirements stay consistent throughout generated output."""

import json
import re

from ..common import CommandRunner, IS_WINDOWS, ProjectWorkspace, ScaffoldFixture, launcher


class CMakeVersionTests(ScaffoldFixture):
    def assert_requirement(self, version):
        for relative in ("CMakeLists.txt", "scripts/setup.cmake", "scripts/run.cmake"):
            self.assertIn(
                f"cmake_minimum_required(VERSION {version})",
                (self.project / relative).read_text(),
            )
        presets = json.loads((self.project / "CMakePresets.json").read_text())
        self.assertEqual(
            list(presets["cmakeMinimumRequired"].values()),
            [int(part) for part in version.split(".")],
        )
        self.assertEqual(presets["version"], 5)
        CommandRunner.run(["cmake", "--list-presets"], self.project)

    def test_default_uses_running_cmake_version(self):
        output = CommandRunner.run(["cmake", "--version"], self.project).stdout
        version = re.search(r"cmake version (\d+\.\d+\.\d+)", output)[1]
        self.scaffold()
        self.assert_requirement(version)

    def test_native_launcher_selects_older_cmake(self):
        launcher(self.project, "scaffold", "SampleRuntime", "exec", "--cmake-version", "3.24")
        self.assert_requirement("3.24.0")
        workflow = (self.project / ".github/workflows/validate.yml").read_text()
        self.assertIn('cmake~=3.24.0', workflow)

    def test_invalid_or_unsupported_version_preserves_existing_output(self):
        self.scaffold()
        original = ProjectWorkspace.snapshot(self.project)
        for version in ("3.5", "3.20", "3.21", "3.23", "2.8", "999.0", "3", "3.21.x", "03.21", "3.21;bad"):
            with self.subTest(version=version):
                self.scaffold(cmake_version=version, force=True, success=False)
                self.assertEqual(ProjectWorkspace.snapshot(self.project), original)

    def test_missing_version_is_rejected_before_generation(self):
        extension = ".bat" if IS_WINDOWS else ".sh"
        script = self.project / ("scaffold-here" + extension)
        invocation = ["cmd", "/c", script] if IS_WINDOWS else [script]
        original = ProjectWorkspace.snapshot(self.project)
        result = CommandRunner.run(
            [*invocation, "SampleRuntime", "exec", "--cmake-version"],
            self.project, success=False,
        )
        self.assertIn("requires a version", result.stdout)
        self.assertEqual(ProjectWorkspace.snapshot(self.project), original)

    def test_both_project_types_configure_with_selected_minimum(self):
        # A config-only imported dependency isolates CMake/compiler compatibility;
        # --full separately builds against the real fmt package from vcpkg.
        prefix = self.workspace / "configuration dependency"
        prefix.mkdir()
        (prefix / "fmt-config.cmake").write_text("add_library(fmt::fmt INTERFACE IMPORTED)\n")
        for project_type in ("exec", "library"):
            with self.subTest(project_type=project_type):
                self.scaffold(project_type=project_type, cmake_version="3.24", force=True)
                CommandRunner.run(
                    [
                        "cmake", "-S", self.project, "-B", self.project / "build/check",
                        "-G", "Ninja", f"-Dfmt_DIR={prefix}",
                    ],
                    self.project,
                )
