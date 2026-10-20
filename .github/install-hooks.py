#!/usr/bin/env python3
"""Enable tracked validation hooks for this clone without changing global Git settings."""

from pathlib import Path
import subprocess

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
HOOKS_PATH = ".github/hooks"


def main():
    result = subprocess.run(
        ["git", "config", "--local", "--get", "core.hooksPath"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        result.check_returncode()
    existing_path = result.stdout.strip()
    if existing_path and existing_path != HOOKS_PATH:
        raise SystemExit(
            f"Existing local core.hooksPath is {existing_path!r}. "
            "Integrate these hooks with your existing hooks before changing it."
        )

    for filename in ("pre-commit", "pre-merge-commit"):
        hook = REPOSITORY_ROOT / HOOKS_PATH / filename
        hook.chmod(hook.stat().st_mode | 0o111)

    subprocess.run(
        ["git", "config", "--local", "core.hooksPath", HOOKS_PATH],
        cwd=REPOSITORY_ROOT,
        check=True,
    )
    print("Installed commit and merge validation hooks for this clone.")


if __name__ == "__main__":
    main()
