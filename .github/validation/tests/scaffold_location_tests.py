from pathlib import Path

from ..common import (
    CommandRunner,
    IS_WINDOWS,
    ProjectWorkspace,
    ScaffoldFixture,
    scaffold,
)


# MARK: Scaffold Location Tests
class ScaffoldLocationTests(ScaffoldFixture):
    def native_command(self, name, *arguments):
        extension = ".bat" if IS_WINDOWS else ".sh"
        script = self.project / (name + extension)
        if IS_WINDOWS:
            return ["cmd", "/c", str(script), *arguments]
        return [script, *arguments]

    def test_external_destinations_keep_the_scaffold_source(self):
        source_contents = ProjectWorkspace.snapshot(self.project)
        for project_type in ("exec", "library"):
            destination = self.workspace / f"generated {project_type}"
            scaffold(
                self.project, "Sample Project", project_type, destination=destination
            )
            self.assertTrue((destination / "CMakeLists.txt").is_file())
            self.assertFalse((destination / ".scaffold").exists())
            self.assertFalse((destination / "scaffold-here.sh").exists())
            self.assertEqual(ProjectWorkspace.snapshot(self.project), source_contents)

    def test_native_launcher_resolves_relative_location_from_the_caller(self):
        CommandRunner.run(
            self.native_command(
                ".scaffold/scaffold", "generated project", "SampleRuntime", "exec"
            ),
            self.workspace,
        )
        self.assertTrue((self.workspace / "generated project/src/main.cpp").is_file())
        self.assertFalse((self.project / "src").exists())

    def test_root_launcher_uses_its_root_from_another_directory(self):
        CommandRunner.run(
            self.native_command("scaffold-here", "SampleRuntime", "exec"),
            self.workspace,
        )
        self.assertTrue((self.project / "src/main.cpp").is_file())
        self.assertTrue((self.project / ".scaffold/scaffold.sh").is_file())
        self.assertFalse((self.workspace / "src").exists())

    def test_destination_is_required(self):
        result = CommandRunner.run(
            self.native_command(".scaffold/scaffold"), self.workspace, success=False
        )
        self.assertIn("Usage:", result.stdout)

    def test_invalid_locations_preserve_the_source(self):
        existing_file = self.workspace / "existing file"
        existing_file.write_text("keep")
        original_contents = ProjectWorkspace.snapshot(self.project)
        for destination in (
            self.project / ".scaffold/templates",
            self.project / ".scaffold",
            Path(self.project.anchor),
            existing_file,
            self.workspace / "bad;location",
        ):
            with self.subTest(destination=destination):
                scaffold(
                    self.project,
                    "SampleRuntime",
                    "exec",
                    destination=destination,
                    force=True,
                    success=False,
                )
                self.assertEqual(
                    ProjectWorkspace.snapshot(self.project), original_contents
                )
        self.assertEqual(existing_file.read_text(), "keep")
