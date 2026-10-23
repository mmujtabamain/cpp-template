"""Exercise scaffold module APIs without running the scaffold entry point."""

import json
import stat

from ..common import CommandRunner, IS_WINDOWS, ProjectWorkspace, ScaffoldFixture


class ScaffoldModuleTests(ScaffoldFixture):
    def run_module(self, module, body="", **options):
        script = self.workspace / "module-test.cmake"
        script.write_text(
            "cmake_minimum_required(VERSION 3.24)\n"
            f'include("{self.project.as_posix()}/.scaffold/scripts/scaffold/{module}.cmake")\n'
            + body
        )
        return CommandRunner.run(["cmake", "-P", script], self.workspace, **options)

    def test_imports_are_independent_and_have_no_project_side_effects(self):
        original = ProjectWorkspace.snapshot(self.project)
        for module in ("utils", "inputs", "identity", "compatibility", "render", "verify-output", "replace"):
            with self.subTest(module=module):
                self.run_module(module, r"""
foreach(variable PROJECT_NAME PROJECT_ROOT PROJECT_TYPE STAGING_DIRECTORY ARG IDENTIFIER_WORDS)
    if(DEFINED ${variable})
        message(FATAL_ERROR "Import leaked application variable: ${variable}")
    endif()
endforeach()
""")
                self.assertEqual(ProjectWorkspace.snapshot(self.project), original)

    def test_input_validation_returns_a_request_without_using_cli_globals(self):
        self.run_module("inputs", f"""
set(PROJECT_DISPLAY_NAME "Wrong Name")
set(PROJECT_TYPE library)
set(SCAFFOLD_GIT ON)
set(SCAFFOLD_DESTINATION "{self.project.as_posix()}/.scaffold")
scaffold_validate_inputs(
    DESTINATION "{self.workspace.as_posix()}/new project" DISPLAY_NAME "  Explicit App  "
    TYPE EXEC COPY_GIT OFF CMAKE_VERSION "3.8" CPP_VERSION "14"
    SCAFFOLD_ROOT "{self.project.as_posix()}/.scaffold" OUTPUT request)
file(WRITE "{self.workspace.as_posix()}/request.json" "${{request}}")
if(NOT PROJECT_DISPLAY_NAME STREQUAL "Wrong Name" OR NOT SCAFFOLD_GIT STREQUAL "ON")
    message(FATAL_ERROR "Validation changed caller variables")
endif()
""")
        request = json.loads((self.workspace / "request.json").read_text())
        self.assertEqual(request["display_name"], "Explicit App")
        self.assertEqual((request["type"], request["copy_git"]), ("exec", "OFF"))
        self.assertEqual((request["cmake_version"], request["cpp_version"]), ("3.8", "14"))
        self.assertFalse((self.workspace / "new project").exists())

    def test_identity_and_versions_are_repeatable_explicit_values(self):
        self.run_module("identity", f"""
include("{self.project.as_posix()}/.scaffold/scripts/scaffold/compatibility.cmake")
set(PROJECT_NAME "caller sentinel")
set(PROJECT_CMAKE_VERSION "999.0")
set(PROJECT_CPP_VERSION "98")
scaffold_project_identity("First Library" first)
scaffold_project_identity("Other Library" second)
string(JSON first_name GET "${{first}}" name)
string(JSON second_name GET "${{second}}" name)
if(NOT first_name STREQUAL "FirstLibrary" OR NOT second_name STREQUAL "OtherLibrary")
    message(FATAL_ERROR "Identity results interfered with each other")
endif()
scaffold_resolve_compatibility(
    MANIFEST "{self.project.as_posix()}/.scaffold/compatibility.json"
    RUNNING_CMAKE_VERSION "3.24.3" CPP_VERSION "14" CMAKE_VERSION "3.8" OUTPUT old)
scaffold_resolve_compatibility(
    MANIFEST "{self.project.as_posix()}/.scaffold/compatibility.json"
    RUNNING_CMAKE_VERSION "3.24.3" OUTPUT current)
file(WRITE "{self.workspace.as_posix()}/old.json" "${{old}}")
file(WRITE "{self.workspace.as_posix()}/current.json" "${{current}}")
if(NOT PROJECT_NAME STREQUAL "caller sentinel" OR NOT PROJECT_CMAKE_VERSION STREQUAL "999.0"
   OR NOT PROJECT_CPP_VERSION STREQUAL "98")
    message(FATAL_ERROR "Function changed caller variables")
endif()
""")
        old = json.loads((self.workspace / "old.json").read_text())
        current = json.loads((self.workspace / "current.json").read_text())
        self.assertEqual((old["cmake_version"], old["cpp_version"], old["use_presets"]), ("3.8.0", "14", "OFF"))
        self.assertEqual((current["cmake_version"], current["cpp_version"]), ("3.24.3", "23"))

    def test_render_and_read_only_verification_use_explicit_arguments(self):
        stage = self.workspace / "explicit staging"
        # Hand-built values ensure rendering does not depend on imports or earlier calls.
        records = {
            "request": dict(display_name="Isolated App", type="exec", copy_git="OFF"),
            "identity": dict(name="IsolatedApp", namespace="isolated_app", macro="ISOLATED_APP", manifest_name="isolated-app"),
            "versions": dict(cmake_version="3.8.0", cmake_major="3", cmake_minor="8", cmake_patch="0",
                             cpp_version="14", cpp_feature="cxx_std_14", use_presets="OFF", preset_schema="3"),
        }
        body = "\n".join(f"set({name} [=[{json.dumps(value)}]=])" for name, value in records.items())
        self.run_module("render", body + f"""
set(PROJECT_TYPE library)
set(PROJECT_NAME WrongName)
set(PROJECT_CMAKE_VERSION 999.0)
set(SCAFFOLD_GIT ON)
set(STAGING_DIRECTORY "{self.project.as_posix()}")
scaffold_render_project(
    TEMPLATE_DIRECTORY "{self.project.as_posix()}/.scaffold/templates"
    STAGING_DIRECTORY "{stage.as_posix()}"
    REQUEST "${{request}}" IDENTITY "${{identity}}" VERSIONS "${{versions}}")
if(NOT PROJECT_NAME STREQUAL "WrongName" OR NOT PROJECT_TYPE STREQUAL "library")
    message(FATAL_ERROR "Rendering leaked template variables")
endif()
""")
        cmake = (stage / "CMakeLists.txt").read_text()
        self.assertIn("cxx_std_14", cmake)
        self.assertIn("IsolatedApp", cmake)
        self.assertFalse((stage / "CMakePresets.json").exists())
        self.assertFalse((stage / ".githooks").exists())
        (stage / "setup.sh").chmod(0o644)
        original = ProjectWorkspace.snapshot(stage)
        self.run_module("verify-output", f"""
set(PROJECT_TYPE library)
set(STAGING_DIRECTORY "{self.project.as_posix()}")
scaffold_verify_output(STAGING_DIRECTORY "{stage.as_posix()}"
    TYPE exec NAME IsolatedApp NAMESPACE isolated_app COPY_GIT OFF USE_PRESETS OFF)
""")
        self.assertEqual(ProjectWorkspace.snapshot(stage), original)
        if not IS_WINDOWS:
            self.assertEqual(stat.S_IMODE((stage / "setup.sh").stat().st_mode), 0o644)

    def test_replacement_returns_status_and_preserves_unrelated_files(self):
        destination = self.workspace / "destination"
        destination.mkdir()
        (destination / ".git").mkdir()
        (destination / ".git/config").write_text("Git belongs to the user")
        (destination / "notes.txt").write_text("keep")
        (destination / "CMakeLists.txt").write_text("previous project")

        def staging(name):
            stage = self.workspace / name
            stage.mkdir()
            for path in ("setup.sh", "run.sh", "CMakeLists.txt"):
                (stage / path).write_text("replacement")
            return stage

        stage = staging("first stage")
        self.run_module("replace", f"""
set(PROJECT_ROOT "{self.project.as_posix()}")
scaffold_replace_project(DESTINATION "{destination.as_posix()}"
    STAGING_DIRECTORY "{stage.as_posix()}" FORCE ON OUTPUT installed)
if(NOT installed OR NOT PROJECT_ROOT STREQUAL "{self.project.as_posix()}")
    message(FATAL_ERROR "Explicit installation result or caller state is wrong")
endif()
""")
        self.assertFalse(stage.exists())
        self.assertEqual((destination / "CMakeLists.txt").read_text(), "replacement")
        self.assertEqual((destination / ".git/config").read_text(), "Git belongs to the user")
        self.assertEqual((destination / "notes.txt").read_text(), "keep")
        original = ProjectWorkspace.snapshot(destination)
        stage = staging("declined stage")
        self.run_module("replace", f"""
scaffold_replace_project(DESTINATION "{destination.as_posix()}"
    STAGING_DIRECTORY "{stage.as_posix()}" FORCE OFF OUTPUT installed)
if(installed)
    message(FATAL_ERROR "Declined replacement reported success")
endif()
file(WRITE "{self.workspace.as_posix()}/continued" "yes")
""", input="n\n")
        self.assertEqual(ProjectWorkspace.snapshot(destination), original)
        self.assertFalse(stage.exists())
        self.assertTrue((self.workspace / "continued").exists())

    def test_direct_module_calls_reject_destructive_path_overlap(self):
        original = ProjectWorkspace.snapshot(self.project)
        self.run_module("render", f"""
scaffold_render_project(
    TEMPLATE_DIRECTORY "{self.project.as_posix()}/.scaffold/templates"
    STAGING_DIRECTORY "{self.project.as_posix()}"
    REQUEST "{{}}" IDENTITY "{{}}" VERSIONS "{{}}")
""", success=False)
        self.assertEqual(ProjectWorkspace.snapshot(self.project), original)
        stage = self.project / "src/staging"
        stage.mkdir(parents=True)
        original = ProjectWorkspace.snapshot(self.project)
        result = self.run_module("replace", f"""
scaffold_replace_project(DESTINATION "{self.project.as_posix()}"
    STAGING_DIRECTORY "{stage.as_posix()}" FORCE ON OUTPUT installed)
""", success=False)
        self.assertIn("Staging must be outside generated paths", result.stdout)
        self.assertEqual(ProjectWorkspace.snapshot(self.project), original)

    def test_utils_preserve_strings_across_record_boundaries(self):
        value = 'quote " slash \\ semicolon ;\nsecond line\tend'
        self.run_module("utils", f"""
scaffold_json_object(record value [=[{value}]=] empty "")
file(WRITE "{self.workspace.as_posix()}/record.json" "${{record}}")
""")
        self.assertEqual(json.loads((self.workspace / "record.json").read_text()), {"value": value, "empty": ""})
