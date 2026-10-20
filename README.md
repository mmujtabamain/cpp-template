# cpp-template

Generate an executable or an installable static/shared C++23 library from this
repository template. macOS and Windows use the same CMake implementations.

Prerequisites: CMake 3.24+, Ninja, Git, and a C++23 compiler (Xcode command line
tools on macOS; Visual Studio C++ tools and a Developer Command Prompt on Windows).

```sh
./scaffold.sh
./setup.sh
./run.sh
```

On Windows use `scaffold.bat`, `setup.bat`, and `run.bat`. Scaffold asks for a
display name and `exec` or `library`. For example, `Sample Library` becomes the
CMake/package target `SampleLibrary`, namespace/header directory `sample_library`,
and vcpkg manifest name `sample-library`.

For automation:

```sh
./scaffold.sh "Sample Library" library
# Explicit destructive recovery, without an interactive prompt:
./scaffold.sh "Sample Library" library --force
```

Batch accepts the same arguments. You can also call CMake directly:

```sh
cmake "-DPROJECT_DISPLAY_NAME=Sample Library" -DPROJECT_TYPE=library -P .template/scripts/scaffold.cmake
```

Scaffold validates and renders a complete replacement before asking to erase an
existing project. The default answer is no. Confirmation (or `SCAFFOLD_FORCE=ON`)
permanently replaces generated sources, headers, assets, examples, tests,
CMake files, README, scripts, the generated CI workflow, build output, and
installed dependencies. It
preserves Git, `.template/`, scaffold launchers, `external/vcpkg/`, and unrelated
files. Names must start with an ASCII letter and use letters, digits, spaces,
underscores or hyphens; reserved identifiers are rejected.

Scaffold runs once to create a project. Setup is repeatable local machine setup:
it clones current vcpkg when absent, removes its `.git`, bootstraps it, installs
the `vcpkg.json` manifest, and configures a development preset. Run configures
and builds CMake's `run` target (the application or library example). Both accept
an optional `release` argument; debug is the default. vcpkg is ignored local
tooling, with no submodule, pinned revision, or hardcoded triplet.

After generation, follow the generated README. Another developer cloning the
project only runs setup and run. You may remove `.template/`, `scaffold.sh`, and
`scaffold.bat` after accepting the generated project; it has no dependency on
template machinery.

Template sources live under `.template/`; validation lives under `.github/validation/`. Run validation with:

```sh
python3 .github/validate.py
python3 .github/validate.py --integration
```

The integration mode uses real upstream vcpkg and fmt and requires network
access. GitHub Actions runs it on macOS and Windows, including installed static
and shared library consumers. Scaffold-only validation requires just Python
and CMake; hook tests also require Git. Validation uses disposable copies and
never regenerates the project in your working directory.

## Commit and merge validation

Enable the tracked hooks once in each clone:

```sh
python3 .github/install-hooks.py
```

Use `python` on Windows. The installer sets the clone's local `core.hooksPath`
to `.github/hooks`; it leaves an existing custom local hook path alone. Hooks
prefer Python from `.venv/`, then fall back to Python on `PATH`.

Every commit and automatic merge commit runs the fast suite against a disposable
copy of the **Git index**, including partially staged changes. A validation
failure blocks commits to `main`. Other branches print a warning and allow the
commit. Missing validation files or tools follow the same policy. The fast suite
checks generation, replacement safety, setup failures, and Git hook behavior.
Real dependency builds run in CI, or locally with `--integration`.

GitHub Actions runs the full suite on macOS and Windows for pushes, pull requests,
and merge queues. Failures block the `Required validation` check for `main` and
pull requests targeting `main`; other branches receive warnings. Generated
projects keep that same check name and validate their own builds and tests.

Import [the main branch ruleset](.github/rulesets/protect-main.json) in GitHub
under **Settings → Rules → Rulesets → New ruleset → Import a ruleset**. Tracking
the JSON does not activate it; import it for this repository and any new repository
created from the template. It requires pull requests and an up-to-date successful
`Required validation` check, blocks deletion and force pushes, and has no bypass
actors or mandatory review approvals. See [GitHub's ruleset import documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository).

Local hooks can be bypassed with `--no-verify` and do not run for fast-forward
merges. The GitHub ruleset supplies the server-side merge requirement. See
[Git's hook documentation](https://git-scm.com/docs/githooks) and
[GitHub's required-check documentation](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).
