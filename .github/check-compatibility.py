#!/usr/bin/env python3
"""Build generated projects with a selected CMake runtime and real installed fmt."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from scripts.common import CommandRunner, IS_WINDOWS, ProjectWorkspace, REPOSITORY_ROOT, scaffold


def version_parts(value):
    return tuple(int(part) for part in value.split("."))


def check(runtime, driver, fmt_prefix):
    output = CommandRunner.run([runtime, "--version"], REPOSITORY_ROOT).stdout
    version = re.search(r"cmake version (\d+\.\d+\.\d+)", output)[1]
    manifest = json.loads((REPOSITORY_ROOT / ".scaffold/compatibility.json").read_text())
    standards = [row["standard"] for row in manifest["cppStandards"]
                 if version_parts(version) >= version_parts(row["cmakeMinimum"])]
    if not standards:
        raise RuntimeError(f"CMake {version} has no supported combinations")
    ctest = runtime.with_name("ctest.exe" if IS_WINDOWS else "ctest")
    with tempfile.TemporaryDirectory(prefix="cpp-template-compatibility-") as directory:
        workspace = Path(directory)
        source = ProjectWorkspace().create(workspace, "scaffold source")
        for standard in standards:
            for kind in ("exec", "library"):
                for shared in ((False, True) if kind == "library" else (False,)):
                    label = f"CMake {version}, C++{standard}, {kind}, shared={shared}"
                    print(label, flush=True)
                    project = workspace / f"cpp{standard}-{kind}-{shared}"
                    scaffold(source, "Compatibility Sample", kind, destination=project,
                             cmake_version=version, cpp_version=standard, cmake_executable=driver)
                    build = project / "build/debug"
                    build.mkdir(parents=True)
                    install = project / "installed"
                    CommandRunner.run(
                        [runtime, "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Debug",
                         f"-DCMAKE_PREFIX_PATH={fmt_prefix}", f"-DCMAKE_INSTALL_PREFIX={install}",
                         f"-DBUILD_SHARED_LIBS={'ON' if shared else 'OFF'}", project], build,
                    )
                    CommandRunner.run([runtime, "--build", "."], build)
                    CommandRunner.run([runtime, "--build", ".", "--target", "run"], build)
                    if kind == "library":
                        CommandRunner.run([ctest, "--output-on-failure"], build)
                        CommandRunner.run([runtime, "--build", ".", "--target", "install"], build)
                        # Verify transitive standard requirements and installed exports too.
                        consumer = project / "consumer"
                        consumer.mkdir()
                        (consumer / "main.cpp").write_text(
                            '#include <compatibility_sample/compatibility_sample.hpp>\n'
                            'int main() { return compatibility_sample::add(2, 3) == 5 ? 0 : 1; }\n'
                        )
                        (consumer / "CMakeLists.txt").write_text(
                            f'cmake_minimum_required(VERSION {version})\n'
                            'project(Consumer LANGUAGES CXX)\n'
                            'find_package(CompatibilitySample CONFIG REQUIRED)\n'
                            'add_executable(consumer main.cpp)\n'
                            'target_link_libraries(consumer PRIVATE CompatibilitySample::CompatibilitySample)\n'
                        )
                        consumer_build = consumer / "build"
                        consumer_build.mkdir()
                        CommandRunner.run(
                            [runtime, "-G", "Ninja", f"-DCMAKE_PREFIX_PATH={install};{fmt_prefix}", consumer],
                            consumer_build,
                        )
                        CommandRunner.run([runtime, "--build", "."], consumer_build)
                        environment = dict(os.environ)
                        environment["PATH"] = os.pathsep.join([
                            str(install / "bin"), str(fmt_prefix / "bin"),
                            environment.get("PATH", ""),
                        ])
                        CommandRunner.run(
                            [consumer_build / ("consumer.exe" if IS_WINDOWS else "consumer")],
                            consumer_build, environment=environment,
                        )
    print(f"Passed all {len(standards)} supported C++ standards with CMake {version}.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cmake", type=Path, required=True)
    parser.add_argument("--driver", default=shutil.which("cmake"))
    parser.add_argument("--fmt-prefix", type=Path, required=True)
    args = parser.parse_args()
    check(args.cmake.resolve(), args.driver, args.fmt_prefix.resolve())


if __name__ == "__main__":
    main()
