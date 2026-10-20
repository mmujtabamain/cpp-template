import json
from ..common import command, fresh, launcher, scaffold, ScaffoldFixture


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
                    self.assertRegex(
                        (project / "CMakeLists.txt").read_text(),
                        rf"project\(\s*{target_name}\s+VERSION",
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
