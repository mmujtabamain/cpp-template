#!/usr/bin/env python3
"""Git hook entry point; keep imports independent of the caller's directory."""

from pathlib import Path
import sys

GITHUB_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GITHUB_DIRECTORY))

from validation.git_hooks import CommitValidation, GitRepository, StagedValidator

if __name__ == "__main__":
    raise SystemExit(
        CommitValidation(
            GitRepository(GITHUB_DIRECTORY.parent), StagedValidator()
        ).run()
    )
