"""Build against real vcpkg/fmt and verify installed library consumers."""

import os
from pathlib import Path
import shutil
import tempfile
from textwrap import dedent
import unittest

from ..common import IS_WINDOWS, CommandRunner, ProjectWorkspace, launcher, scaffold

# MARK: Real dependency lifecycle


class IntegrationTests(unittest.TestCase):
    """Keep dependent build phases in one test with explicit resource ownership."""

    def test_complete_project_lifecycle(self):
        with tempfile.TemporaryDirectory(
            prefix="cpp-template-integration-"
        ) as directory:
            workspace = Path(directory)
            project, vcpkg_directory = self._validate_executable(workspace)
            library_project, dependency_prefix = self._validate_library(
                workspace, project, vcpkg_directory
            )
            self._validate_subdirectory_consumer(
                workspace, library_project, dependency_prefix
            )

    # MARK: Executable setup, sources, assets, and configurations

    def _validate_executable(self, workspace):
        project = ProjectWorkspace().create(workspace, "integration executable")
        scaffold(project, "SampleRuntime", "exec")
        print(
            "Integration: first setup (clone/bootstrap/install/configure)", flush=True
        )
        launcher(project, "setup")
        vcpkg_directory = project / "external/vcpkg"
        self.assertFalse((vcpkg_directory / ".git").exists())
        vcpkg_executable = vcpkg_directory / ("vcpkg.exe" if IS_WINDOWS else "vcpkg")
        executable_identity = (
            vcpkg_executable.stat().st_mtime_ns,
            vcpkg_executable.stat().st_size,
        )
        reuse_marker = vcpkg_directory / "reuse-marker"
        reuse_marker.write_text("keep")
        (project / "build/keep").write_text("build survives setup")
        print("Integration: repeated setup and executable run", flush=True)
        launcher(project, "setup")
        self.assertEqual(
            executable_identity,
            (vcpkg_executable.stat().st_mtime_ns, vcpkg_executable.stat().st_size),
        )
        self.assertEqual(reuse_marker.read_text(), "keep")
        self.assertTrue((project / "build/keep").exists())
        (project / "assets/check.txt").write_text("copied asset")
        (project / "src/util").mkdir()
        (project / "src/util/extra.cpp").write_text("int extra() { return 42; }\n")
        (project / "src/util/extra.hpp").write_text("int extra();\n")
        main_source = project / "src/main.cpp"
        main_source.write_text(
            '#include "util/extra.hpp"\n'
            + main_source.read_text().replace(
                "fmt::print(", "if (extra() != 42) return 1;\n    fmt::print("
            )
        )
        result = launcher(project, "run")
        self.assertIn("Hello from SampleRuntime!", result.stdout)
        self.assertEqual(
            (project / "build/debug/assets/check.txt").read_text(), "copied asset"
        )
        launcher(project, "setup", "release")
        launcher(project, "run", "release")
        # Multi-config generators must run the real target and copy assets beside it.
        CommandRunner.run(
            [
                "cmake",
                "-S",
                project,
                "-B",
                project / "build/multi",
                "-G",
                "Ninja Multi-Config",
                f"-DCMAKE_TOOLCHAIN_FILE={vcpkg_directory}/scripts/buildsystems/vcpkg.cmake",
                f"-DVCPKG_INSTALLED_DIR={project}/vcpkg_installed",
                "-DVCPKG_MANIFEST_INSTALL=OFF",
            ],
            project,
        )
        CommandRunner.run(
            [
                "cmake",
                "--build",
                project / "build/multi",
                "--config",
                "Debug",
                "--target",
                "run",
            ],
            project,
        )
        self.assertTrue((project / "build/multi/Debug/assets/check.txt").exists())

        return project, vcpkg_directory

    # MARK: Static/shared exports and installed consumers

    def _validate_library(self, workspace, project, vcpkg_directory):
        library_project = ProjectWorkspace().create(workspace, "integration library")
        scaffold(library_project, "Sample Library", "library")
        (library_project / "external").mkdir()
        shutil.move(vcpkg_directory, library_project / "external/vcpkg")
        shutil.copytree(
            project / "vcpkg_installed", library_project / "vcpkg_installed"
        )
        # Existing sources with a missing binary must bootstrap without cloning.
        library_vcpkg_executable = (
            library_project
            / "external/vcpkg"
            / ("vcpkg.exe" if IS_WINDOWS else "vcpkg")
        )
        library_vcpkg_executable.unlink()
        launcher(library_project, "setup")
        self.assertTrue(library_vcpkg_executable.exists())
        self.assertEqual(
            (library_project / "external/vcpkg/reuse-marker").read_text(), "keep"
        )
        launcher(library_project, "setup")
        dependency_prefixes = [
            dependency_path
            for dependency_path in (library_project / "vcpkg_installed").iterdir()
            if (dependency_path / "share/fmt").exists()
        ]
        self.assertEqual(len(dependency_prefixes), 1, dependency_prefixes)
        dependency_prefix = dependency_prefixes[0]

        for build_shared_library in (False, True):
            library_kind = "shared" if build_shared_library else "static"
            print(
                f"Integration: {library_kind} library, example, CTest, install and consumer",
                flush=True,
            )
            CommandRunner.run(
                [
                    "cmake",
                    "--preset",
                    "debug",
                    f'-DBUILD_SHARED_LIBS={"ON" if build_shared_library else "OFF"}',
                ],
                library_project,
            )
            launcher(library_project, "run")
            CommandRunner.run(
                ["cmake", "--build", "--preset", "debug"], library_project
            )
            CommandRunner.run(["ctest", "--preset", "debug"], library_project)
            install_prefix = workspace / f"install-{library_kind}"
            CommandRunner.run(
                [
                    "cmake",
                    "--install",
                    library_project / "build/debug",
                    "--prefix",
                    install_prefix,
                    "--config",
                    "Debug",
                ],
                library_project,
            )
            self.assertTrue(
                (install_prefix / "include/sample_library/export.hpp").is_file()
            )
            self.assertTrue(
                list(install_prefix.rglob("SampleLibraryConfigVersion.cmake"))
            )
            self._validate_installed_consumer(
                workspace,
                library_project,
                install_prefix,
                dependency_prefix,
                library_kind,
            )

        return library_project, dependency_prefix

    # MARK: Independent installed-package consumer

    def _validate_installed_consumer(
        self,
        workspace,
        library_project,
        install_prefix,
        dependency_prefix,
        library_kind,
    ):
        consumer = workspace / f"consumer-{library_kind}"
        consumer.mkdir()
        (consumer / "main.cpp").write_text(
            "#include <sample_library/sample_library.hpp>\n\n"
            "int main()\n"
            "{\n"
            "    return sample_library::add(2, 3) == 5 ? 0 : 1;\n"
            "}\n"
        )
        (consumer / "CMakeLists.txt").write_text(dedent("""\
                cmake_minimum_required(VERSION 3.24)
                project(Consumer LANGUAGES CXX)

                find_package(SampleLibrary 0.1 CONFIG REQUIRED)

                add_executable(consumer main.cpp)
                target_link_libraries(consumer PRIVATE SampleLibrary::SampleLibrary)
                """))
        # Hide original public/private sources: the installed package must suffice.
        for directory in ("src", "include"):
            (library_project / directory).rename(
                library_project / (directory + "-hidden")
            )
        try:
            CommandRunner.run(
                [
                    "cmake",
                    "-S",
                    consumer,
                    "-B",
                    consumer / "build",
                    "-G",
                    "Ninja",
                    "-DCMAKE_BUILD_TYPE=Debug",
                    f"-DCMAKE_PREFIX_PATH={install_prefix};{dependency_prefix}",
                ],
                consumer,
            )
            CommandRunner.run(["cmake", "--build", consumer / "build"], consumer)
            environment = os.environ.copy()
            environment["PATH"] = os.pathsep.join(
                [
                    str(install_prefix / "bin"),
                    str(dependency_prefix / "debug/bin"),
                    str(dependency_prefix / "bin"),
                    environment.get("PATH", ""),
                ]
            )
            CommandRunner.run(
                [consumer / "build" / ("consumer.exe" if IS_WINDOWS else "consumer")],
                consumer,
                environment=environment,
            )
        finally:
            for directory in ("src", "include"):
                (library_project / (directory + "-hidden")).rename(
                    library_project / directory
                )

    # MARK: Embedded library and template independence

    def _validate_subdirectory_consumer(
        self, workspace, library_project, dependency_prefix
    ):
        print("Integration: add_subdirectory consumer defaults", flush=True)
        consumer_project = workspace / "subdirectory-consumer"
        consumer_project.mkdir()
        (consumer_project / "CMakeLists.txt").write_text(dedent(f"""\
                cmake_minimum_required(VERSION 3.24)
                project(Outer LANGUAGES CXX)

                add_subdirectory("{library_project.as_posix()}" library)

                if(SAMPLE_LIBRARY_BUILD_EXAMPLES OR SAMPLE_LIBRARY_BUILD_TESTS)
                    message(FATAL_ERROR "Consumer unexpectedly enabled examples/tests")
                endif()

                if(TARGET SampleLibrary_example OR TARGET SampleLibrary_test)
                    message(FATAL_ERROR "Consumer contains development targets")
                endif()
                """))
        CommandRunner.run(
            [
                "cmake",
                "-S",
                consumer_project,
                "-B",
                consumer_project / "build",
                "-G",
                "Ninja",
                f"-DCMAKE_PREFIX_PATH={dependency_prefix}",
            ],
            consumer_project,
        )
        CommandRunner.run(
            ["cmake", "--build", consumer_project / "build"], consumer_project
        )
        # Removing template machinery must leave the generated project fully usable.
        shutil.rmtree(library_project / ".template")
        (library_project / "scaffold.sh").unlink()
        (library_project / "scaffold.bat").unlink()
        launcher(library_project, "run")
        print("Integration checks passed", flush=True)
