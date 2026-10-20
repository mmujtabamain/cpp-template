import os
from pathlib import Path
import subprocess
import sys
import tempfile


# MARK: Git Repository
class GitRepository:
    """Export the proposed commit without stashing or changing working files."""

    def __init__(self, root):
        self.root = Path(root)

    def current_branch(self):
        result = subprocess.run(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 1:
            return "HEAD"  # Detached commits have no main-branch policy.
        result.check_returncode()
        return result.stdout.strip()

    def export_index(self, destination):
        # checkout-index preserves executable modes and honors GIT_INDEX_FILE,
        # including the temporary index Git uses for `commit --only`.
        subprocess.run(
            ["git", "checkout-index", "--all", f"--prefix={destination.as_posix()}/"],
            cwd=self.root,
            check=True,
        )


# MARK: Staged Validator
class StagedValidator:
    """Execute validation from an isolated snapshot using the current Python."""

    def validate(self, snapshot, *, integration=False):
        if not (snapshot / ".template").is_dir():
            # Generated projects can remove the template machinery entirely.
            if (snapshot / "CMakeLists.txt").is_file():
                print(
                    "Template sources removed; generated-project CI handles builds.",
                    flush=True,
                )
                return 0
            raise RuntimeError("Staged template sources are missing.")

        validation_script = snapshot / ".github/validate.py"
        if not validation_script.is_file():
            raise RuntimeError("The staged .github/validate.py is missing.")

        # Git's hook environment points at the real repository. Do not leak it
        # into validation scenarios that create and commit disposable repositories.
        environment = {
            name: value
            for name, value in os.environ.items()
            if not name.startswith("GIT_")
        }
        arguments = [sys.executable, str(validation_script)]
        if integration:
            arguments.append("--full")

        result = subprocess.run(
            arguments,
            cwd=snapshot,
            env=environment,
            check=False,
        )
        return result.returncode


# MARK: Commit Validation
class CommitValidation:
    """Apply main-branch enforcement to an independently replaceable validator."""

    def __init__(self, repository, validator):
        self.repository = repository
        self.validator = validator

    def run(self):
        # If branch detection itself fails, do not guess and permit a main commit.
        try:
            branch = self.repository.current_branch()
        except (OSError, subprocess.SubprocessError) as error:
            print(f"ERROR: Cannot determine commit branch: {error}", file=sys.stderr)
            return 1

        print(f"Validating staged template on {branch}...", flush=True)
        try:
            with tempfile.TemporaryDirectory(prefix="cpp-template-index-") as directory:
                snapshot = Path(directory)
                self.repository.export_index(snapshot)
                # main commits must prove generated projects actually build;
                # development branches use the fast suite for early feedback.
                validation_status = self.validator.validate(
                    snapshot, integration=branch == "main"
                )
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            print(f"Validation could not complete: {error}", file=sys.stderr)
            validation_status = 1

        if validation_status == 0:
            return 0
        if branch == "main":
            print(
                "ERROR: Template validation failed; commit to main blocked.",
                file=sys.stderr,
            )
            return 1

        print(
            f"WARNING: Template validation failed on {branch}; commit allowed. "
            "Fix validation before merging into main.",
            file=sys.stderr,
        )
        return 0
