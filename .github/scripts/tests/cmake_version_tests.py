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
        self.assertEqual(presets["version"], 3)
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
        self.assertIn("cmake-version: '3.24.0'", workflow)

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
        for flag, argument in (("--cmake-version", "version"), ("--cpp-version", "standard")):
            with self.subTest(flag=flag):
                result = CommandRunner.run(
                    [*invocation, "SampleRuntime", "exec", flag],
                    self.project, success=False,
                )
                self.assertIn(f"requires a {argument}", result.stdout)
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

    def test_all_manifest_standards_generate_with_their_minimum(self):
        manifest = json.loads((self.project / ".scaffold/compatibility.json").read_text())
        for row in manifest["cppStandards"]:
            with self.subTest(row=row):
                self.scaffold(cpp_version=row["standard"], cmake_version=row["cmakeMinimum"], force=True)
                cmake = (self.project / "CMakeLists.txt").read_text()
                self.assertIn(f'set(CMAKE_CXX_STANDARD {row["standard"]})', cmake)
                self.assertIn(f'cxx_std_{row["standard"]}', cmake)
                self.assertIn(f'C++{row["standard"]}', (self.project / "README.md").read_text())
                self.assertNotIn("CMAKE_VERSION VERSION_LESS", cmake)
                development = (self.project / "scripts/development.cmake").read_text()
                self.assertNotIn("CMAKE_VERSION VERSION_LESS", development)
                self.assertNotIn("@PROJECT_", development)
                presets = (self.project / "CMakePresets.json").exists()
                self.assertEqual(presets, tuple(map(int, row["cmakeMinimum"].split("."))) >= (3, 21))

    def test_invalid_cpp_and_cmake_pairs_preserve_existing_output(self):
        self.scaffold()
        original = ProjectWorkspace.snapshot(self.project)
        for cpp, cmake in ((98, "3.24"), (26, "3.31"), ("c++17", "3.24"),
                           (11, "3.5"), (17, "3.7"), (20, "3.20"), (23, "3.21")):
            with self.subTest(cpp=cpp, cmake=cmake):
                self.scaffold(cpp_version=cpp, cmake_version=cmake, force=True, success=False)
                self.assertEqual(ProjectWorkspace.snapshot(self.project), original)

    def test_native_launcher_selects_cpp_and_cmake(self):
        launcher(self.project, "scaffold", "SampleRuntime", "exec", "--cpp-version", "14", "--cmake-version", "3.8")
        self.assertFalse((self.project / "CMakePresets.json").exists())
        self.assertIn("cxx_std_14", (self.project / "CMakeLists.txt").read_text())
        self.assertIn("cmake --build build/debug", (self.project / "README.md").read_text())
