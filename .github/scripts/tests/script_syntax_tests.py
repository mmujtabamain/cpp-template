"""Repository checks: parse scripts without executing their commands."""

import ast
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import yaml

from ..common import CommandRunner, REPOSITORY_ROOT


class ScriptSyntaxTests(unittest.TestCase):
    def source_files(self):
        for directory in (".github", ".scaffold"):
            yield from (REPOSITORY_ROOT / directory).rglob("*")
        yield from REPOSITORY_ROOT.glob("*.sh")

    def workflow_commands(self):
        for workflow in self.source_files():
            if workflow.suffix not in (".yml", ".yaml"):
                continue
            document = yaml.safe_load(workflow.read_text())
            if not isinstance(document, dict) or "jobs" not in document:
                continue
            for job in document["jobs"].values():
                runner = job.get("runs-on", "")
                for step in job.get("steps", []):
                    if "run" not in step:
                        continue
                    # GitHub expands expressions before handing commands to a shell.
                    command = re.sub(r"\$\{\{.*?\}\}", "value", step["run"])
                    shell = step.get("shell", job.get("defaults", {}).get("run", {}).get("shell"))
                    if shell:
                        shells = [shell.split()[0]]
                    elif isinstance(runner, str) and "windows" in runner:
                        shells = ["pwsh"]
                    elif isinstance(runner, str) and "matrix.os" in runner:
                        condition = step.get("if", "")
                        if "runner.os == 'Windows'" in condition:
                            shells = ["pwsh"]
                        elif "runner.os != 'Windows'" in condition:
                            shells = ["bash"]
                        else:
                            shells = ["bash", "pwsh"]
                    else:
                        shells = ["bash"]
                    yield workflow, command, shells

    def test_python_sources_parse(self):
        for source in self.source_files():
            if source.suffix == ".py":
                with self.subTest(source=source):
                    ast.parse(source.read_text(), filename=str(source))

    @unittest.skipUnless(shutil.which("bash"), "Bash syntax checks require bash")
    def test_shell_sources_and_workflow_commands_parse(self):
        for source in self.source_files():
            if source.suffix == ".sh" or source.parent.name == "hooks":
                if source.is_file() and source.read_text().startswith("#!/bin/sh"):
                    with self.subTest(source=source):
                        CommandRunner.run(["bash", "-n", source.as_posix()], REPOSITORY_ROOT)
        for workflow, command, shells in self.workflow_commands():
            if "bash" in shells:
                with self.subTest(workflow=workflow, command=command):
                    CommandRunner.run(["bash", "-n"], REPOSITORY_ROOT, input=command)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell syntax checks run on Windows CI")
    def test_powershell_sources_and_workflow_commands_parse(self):
        commands = [
            (source, source.read_text())
            for source in self.source_files() if source.suffix == ".ps1"
        ]
        commands.extend(
            (workflow, command)
            for workflow, command, shells in self.workflow_commands()
            if "pwsh" in shells
        )
        # Hosts may write a startup cache in cwd when the user cache is unwritable.
        with tempfile.TemporaryDirectory(prefix="cpp-template-pwsh-") as directory:
            for source, command in commands:
                with self.subTest(source=source, command=command):
                    CommandRunner.run(
                        [
                            "pwsh", "-NoProfile", "-NonInteractive", "-Command",
                            "$tokens = $null; $errors = $null; "
                            "[void][System.Management.Automation.Language.Parser]::ParseInput("
                            "[Console]::In.ReadToEnd(), [ref]$tokens, [ref]$errors); "
                            "if ($errors.Count) { $errors | Out-String | Write-Error; exit 1 }",
                        ],
                        Path(directory), input=command,
                    )
