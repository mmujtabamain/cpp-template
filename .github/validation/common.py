"""Shared process and disposable-project adapters for validation scenarios."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
IS_WINDOWS = os.name == "nt"


# MARK: Command Runner
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


# MARK: Project Workspace
class ProjectWorkspace:
    """Disposable Project Workspace."""

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
        for filename in (
            "scaffold.sh",
            "scaffold.bat",
            "README.md",
            ".gitignore",
            ".gitattributes",
        ):
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


# MARK: Scaffold Fixture
class ScaffoldFixture(unittest.TestCase):
    """Create a fresh disposable repository for each scenario."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="cpp-template-")
        self.addCleanup(self.temporary_directory.cleanup)
        self.workspace = Path(self.temporary_directory.name)
        self.project = ProjectWorkspace().create(self.workspace, "project with spaces")

    def scaffold(self, name="Sample Library", project_type="library", **options):
        return scaffold(self.project, name, project_type, **options)


def scaffold(
    project,
    name,
    project_type,
    *,
    force=False,
    answer="",
    success=True,
) -> subprocess.CompletedProcess:
    """Exercise shared CMake validation and destructive-replacement confirmation."""
    arguments = [
        "cmake",
        f"-DPROJECT_DISPLAY_NAME={name}",
        f"-DPROJECT_TYPE={project_type}",
    ]
    if force:
        arguments.append("-DSCAFFOLD_FORCE=ON")
    return CommandRunner.run(
        arguments + ["-P", project / ".template/scripts/scaffold.cmake"],
        project,
        input=answer,
        success=success,
    )


def launcher(project, name, *arguments, input="") -> subprocess.CompletedProcess:
    """Exercise the native shell or Batch entry point on this host."""
    if IS_WINDOWS:
        invocation = ["cmd", "/c", str(project / (name + ".bat")), *arguments]
    else:
        invocation = [project / (name + ".sh"), *arguments]
    return CommandRunner.run(invocation, project, input=input)
