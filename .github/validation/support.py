"""Shared process and disposable-project adapters for validation scenarios."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
IS_WINDOWS = os.name == "nt"


# MARK: Process execution


class CommandRunner:
    """Capture diagnostics and check the expected exit status in one place."""

    @staticmethod
    def run(arguments, working_directory, *, input="", environment=None, success=True):
        result = subprocess.run(
            [str(argument) for argument in arguments],
            cwd=working_directory,
            input=input,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=environment,
            timeout=1800,
        )
        if success and result.returncode:
            raise AssertionError(f"Command failed: {arguments}\n{result.stdout}")
        if not success and not result.returncode:
            raise AssertionError(
                f"Command unexpectedly succeeded: {arguments}\n{result.stdout}"
            )
        return result


# Keep test scenarios readable while allowing the process adapter to be replaced.
command = CommandRunner.run


# MARK: Disposable project operations


class ProjectWorkspace:
    """Own file operations without deciding which validation suite should run."""

    def __init__(self, repository_root=REPOSITORY_ROOT):
        self.repository_root = repository_root

    def create(self, workspace, name):
        project = workspace / name
        project.mkdir()
        for directory in (".template", ".github"):
            shutil.copytree(
                self.repository_root / directory,
                project / directory,
                ignore=shutil.ignore_patterns(".scaffold-tmp", "__pycache__"),
            )
        for filename in ("scaffold.sh", "scaffold.bat", "README.md", ".gitignore"):
            shutil.copy2(self.repository_root / filename, project / filename)
        return project

    @staticmethod
    def snapshot(project):
        """Hash files to detect unintended writes on cancellation or rejection."""
        return {
            str(path.relative_to(project)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in project.rglob("*")
            if path.is_file()
        }


fresh = ProjectWorkspace().create
snapshot = ProjectWorkspace.snapshot


def scaffold(
    project,
    name="Sample Library",
    project_type="library",
    *,
    force=False,
    answer="",
    success=True,
):
    """Exercise shared CMake validation and destructive-replacement confirmation."""
    arguments = [
        "cmake",
        f"-DPROJECT_DISPLAY_NAME={name}",
        f"-DPROJECT_TYPE={project_type}",
    ]
    if force:
        arguments.append("-DSCAFFOLD_FORCE=ON")
    return command(
        arguments + ["-P", project / ".template/scripts/scaffold.cmake"],
        project,
        input=answer,
        success=success,
    )


def launcher(project, name, *arguments, input=""):
    """Exercise the native shell or Batch entry point on this host."""
    if IS_WINDOWS:
        invocation = ["cmd", "/c", str(project / (name + ".bat")), *arguments]
    else:
        invocation = [project / (name + ".sh"), *arguments]
    return command(invocation, project, input=input)
