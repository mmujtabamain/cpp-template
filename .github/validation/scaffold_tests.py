"""Fast scaffold and development-script regression tests."""

import json
from pathlib import Path
import tempfile
import unittest

from .support import IS_WINDOWS, command, fresh, launcher, scaffold, snapshot

# MARK: Disposable project fixture


class ScaffoldFixture(unittest.TestCase):
    """Create a fresh disposable repository for each scenario."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="cpp-template-")
        self.addCleanup(self.temporary_directory.cleanup)
        self.workspace = Path(self.temporary_directory.name)
        self.project = fresh(self.workspace, "project with spaces")


# MARK: Naming and native entry points


class ScaffoldGenerationTests(ScaffoldFixture):
    """Verify generated identities, files, and platform launchers."""

    def test_names_and_types(self):
        for project_type, suffix in (("exec", "Runtime"), ("library", "Library")):
            names = [
                (
                    f"Sample{suffix}",
                    f"Sample{suffix}",
                    f"sample_{suffix.lower()}",
                    f"sample-{suffix.lower()}",
                ),
                (
                    f"Sample {suffix}",
                    f"Sample{suffix}",
                    f"sample_{suffix.lower()}",
                    f"sample-{suffix.lower()}",
                ),
                (
                    f"sample-{suffix.lower()}",
                    f"Sample{suffix}",
                    f"sample_{suffix.lower()}",
                    f"sample-{suffix.lower()}",
                ),
            ]
            for index, (
                display_name,
                target_name,
                namespace,
                manifest_name,
            ) in enumerate(names):
                with self.subTest(project_type=project_type, name=display_name):
                    project = fresh(self.workspace, f"{project_type}-{index}")
                    scaffold(project, display_name, project_type)
                    self.assertIn(
                        f"project({target_name} VERSION",
                        (project / "CMakeLists.txt").read_text(),
                    )
                    self.assertEqual(
                        json.loads((project / "vcpkg.json").read_text())["name"],
                        manifest_name,
                    )
                    self.assertEqual(
                        json.loads((project / "vcpkg.json").read_text())[
                            "dependencies"
                        ],
                        ["fmt"],
                    )
                    self.assertIn(display_name, (project / "README.md").read_text())
                    command(["cmake", "--list-presets"], project)
                    workflow = (project / ".github/workflows/validate.yml").read_text()
                    self.assertNotIn(".template/", workflow)
                    self.assertNotIn("@PROJECT_TYPE@", workflow)
                    self.assertIn(f"'{project_type}' == 'library'", workflow)
                    self.assertFalse((project / ".cpp-template-scaffolded").exists())
                    self.assertFalse((project / ".template/.scaffold-tmp").exists())
                    if project_type == "library":
                        header = project / f"include/{namespace}/{namespace}.hpp"
                        self.assertIn(f"namespace {namespace}", header.read_text())
                        self.assertTrue((project / f"src/{namespace}.cpp").is_file())
                        package_config = (
                            project / f"cmake/{target_name}Config.cmake.in"
                        ).read_text()
                        self.assertIn("@PACKAGE_INIT@", package_config)
                        self.assertIn(
                            "find_dependency(fmt CONFIG REQUIRED)", package_config
                        )
                        self.assertIn(
                            f"{target_name}::{target_name}",
                            (project / "README.md").read_text(),
                        )
                    else:
                        self.assertTrue((project / "assets/.gitkeep").is_file())
                        self.assertIn(
                            display_name, (project / "src/main.cpp").read_text()
                        )

    def test_native_launcher(self):
        launcher(self.project, "scaffold", "Sample Library", "library")
        self.assertTrue(
            (self.project / "include/sample_library/sample_library.hpp").exists()
        )

    def test_interactive_launcher(self):
        launcher(self.project, "scaffold", input="SampleRuntime\nexec\n")
        self.assertIn("SampleRuntime", (self.project / "CMakeLists.txt").read_text())


# MARK: Replacement and error recovery


class ScaffoldSafetyTests(ScaffoldFixture):
    """Prove cancellation and invalid input preserve existing work."""

    def test_declined_and_confirmed_replacement(self):
        scaffold(self.project)
        (self.project / "src/valuable.cpp").write_text("user modifications")
        original_contents = snapshot(self.project)
        for answer in ("", "n\n"):
            result = scaffold(self.project, "Replacement", "exec", answer=answer)
            self.assertIn("cancelled", result.stdout)
            self.assertEqual(original_contents, snapshot(self.project))
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
        original_contents = snapshot(self.project)
        for name in ("", "123", "../escape", "bad;name", 'bad"name', "class", "Run"):
            scaffold(self.project, name, force=True, success=False)
            self.assertEqual(original_contents, snapshot(self.project))
        scaffold(self.project, project_type="invalid", force=True, success=False)
        self.assertEqual(original_contents, snapshot(self.project))

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


# MARK: Development environment failures


class DevelopmentScriptTests(ScaffoldFixture):
    """Check setup/run diagnostics without downloading dependencies."""

    def test_run_requires_setup(self):
        scaffold(self.project)
        result = command(
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
        result = command(
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
        result = command(
            ["cmake", "-P", self.project / "scripts/setup.cmake"],
            self.project,
            success=False,
        )
        self.assertIn("Malformed vcpkg tree", result.stdout)
        self.assertEqual((vcpkg_directory / "keep").read_text(), "malformed tree")
