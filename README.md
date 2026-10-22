# cpp-template

Generate an executable or an installable static/shared C++ library from this repository template.

| OS      | Support           | Build CI |
| ------- | ----------------- | -------- |
| Windows | Supported         | ✅       |
| macOS   | Supported         | ✅       |
| Linux   | Not yet validated | -        |

# Prerequisites

CMake 3.24+ to run the scaffold, Ninja, Git, Python 3 for scaffold validation, and a compiler for the selected C++ standard (C++23 by default) (Xcode command line tools on macOS; Visual Studio C++ tools and a Developer Command Prompt on Windows; GCC or Clang on Linux).

**macOS** - with [Homebrew](https://brew.sh/) installed:

```sh
xcode-select --install
brew install cmake ninja git python pkgconf
```

**Windows** - with [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/) installed:

```powershell
winget install --exact --id Kitware.CMake
winget install --exact --id Ninja-build.Ninja
winget install --exact --id Git.Git
winget install --exact --id Python.Python.3.13
winget install --exact --id Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

After installation, open a new Developer Command Prompt for Visual Studio.

**Linux (Ubuntu 24.04+)** - install the compiler, build tools, and [vcpkg prerequisites](https://learn.microsoft.com/en-us/vcpkg/concepts/supported-hosts#dependencies):

```sh
sudo apt update
sudo apt install build-essential cmake ninja-build git python3 curl zip unzip tar pkg-config
```

# Setup

> On Windows, use the corresponding `*.bat` scripts and `python` instead of `python3`.

Run `scaffold-here.sh` with a _project name_ and _type_; `exec` for executable programs or `library` for libraries. Use `--force` to overwrite an existing generated project without confirmation.

```sh
./scaffold-here.sh "SampleRuntime" exec

# or generate into a different directory
./.scaffold/scaffold.sh "../Sample Library" "Sample Library" library
```

> Names must start with an ASCII letter and contain only letters, digits, spaces, underscores, or hyphens; reserved identifiers are rejected. Other naming forms, such as `sample-project`, `SampleProject`, and `sample_project`, are derived automatically.

Templates and launchers stay in `.scaffold/` for reuse. An external destination receives only the generated project. `scaffold-here.sh` always targets this repository's root, even when called from another directory.

### Enable Hooks see [Git hooks](#scaffold-validation-and-generated-project-validation)

Enable the tracked hooks once in each template clone. On Windows, activate the
virtual environment with `.venv\Scripts\activate.bat` instead:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r .github/requirements.txt
python3 .github/install-hooks.py
```

The installer sets the clone's local `core.hooksPath` to `.github/hooks`; it leaves an existing custom local hook path unchanged.

> Hooks prefer Python from `.venv/`, then fall back to Python on `PATH`.

### Run setup script

Run `setup.sh` afterwards to complete setup.

- `./setup.sh` reuses the existing vcpkg clone, installed dependencies, and build output.
- `./setup.sh --clean` starts setup from scratch: it deletes `external/vcpkg/`,
  `vcpkg_installed/`, and `build/`, clones vcpkg again, downloads dependencies
  again, and rebuilds them from source. Binary and asset cache providers are
  disabled for that run, including inherited cache settings. On Windows use
  `setup.bat --clean`.

**Warning:** `--clean` discards local changes in those three directories. It
resets setup state; project sources and the project's `.git` are inputs and stay
intact. Shared caches are bypassed rather than deleted, so other projects are
unaffected. Cleanup must complete before cloning or setup stops with an error.

## C++ and CMake compatibility

Select both versions when scaffolding:

```sh
./scaffold-here.sh "SampleRuntime" exec --cpp-version 14 --cmake-version 3.8
```

C++ defaults to **23**. The generated CMake minimum defaults to the version shown
by `cmake --version` when scaffolding. `major.minor` and `major.minor.patch` are
accepted. This selects requirements for the new project; it does not install a
compiler or switch your local CMake executable.

Allowed pairs are stored in [`.scaffold/compatibility.json`](.scaffold/compatibility.json)
and checked before rendering or replacing any project files:

| C++ standard | Minimum generated CMake | Verification |
| --- | --- | --- |
| 11 | 3.8 | Actual 3.8.2 runtime: executable, static/shared libraries, tests and installed consumers. |
| 14 | 3.8 | Actual 3.8.2 runtime: executable, static/shared libraries, tests and installed consumers. |
| 17 | 3.8 | Actual 3.8.2 runtime: executable, static/shared libraries, tests and installed consumers. |
| 20 | 3.21 | Actual 3.21.4 runtime with the same build and consumer checks. |
| 23 | 3.24 | Actual 3.24.3 and 4.4.2 runtimes with the same build and consumer checks. |

Only these standards and CMake major versions 3 and 4 are accepted. Each CMake
version must meet the selected standard's floor and must not exceed the CMake
running the scaffold. For example, C++23/CMake 3.8 is rejected; C++14/CMake 3.8 is
accepted. Actual compiler support for the selected standard is still required.

The **generated-project floor is now 3.8**. CMake 3.5 cannot express the standard
[standard meta-features](https://cmake.org/cmake/help/latest/prop_gbl/CMAKE_CXX_KNOWN_FEATURES.html)
used by the library's public interface, and the current
[vcpkg toolchain](https://github.com/microsoft/vcpkg/blob/master/scripts/buildsystems/vcpkg.cmake)
itself requires at least 3.7.2. C++20 uses the verified 3.21 floor;
C++23 retains 3.24 for supported-platform compiler recognition. The scaffold
program itself requires 3.24+; generating a project and building that project
are separate operations.

Projects targeting CMake 3.21+ receive shared presets (schema 3). Earlier targets
receive direct configure/build commands and no `CMakePresets.json`. The generator
writes the commands appropriate to the chosen pair once; generated projects have
no CMake-version fallback branches. Documentation for the direct commands lives
in `build-cmake-legacy.md`, where “legacy” refers to the CMake version.

The repository CI runs the full vcpkg lifecycle on macOS and Windows. A separate
runtime matrix builds all allowed standards with CMake 3.8.2, 3.21.4, 3.24.3, and
the latest release, using real fmt and checking installed library consumers.
Third-party packages may impose additional requirements or acquire newer tools
for their own builds. The compatibility manifest describes the shipped templates
and their starter dependencies, not arbitrary dependencies added later.

## Git

Scaffolding copies GitHub CI, the main ruleset, `.gitignore`, and `.gitattributes` by default.

Use `--no-git` to skip these. It does not delete existing Git files, hooks, or rulesets;

Manage repository Git setup and cleanup **yourself**. Existing Git files, `.scaffold/`, unrelated files, and `external/vcpkg/` are preserved; without `--no-git`, matching template files are overwritten.

```sh
# generate without copying Git files
./scaffold-here.sh "SampleRuntime" exec --no-git

# generate externally with the default Git files
./.scaffold/scaffold.sh "../Sample Library" "Sample Library" library
```

## Scaffold validation and generated-project validation

This repository's `.github/validate.py` checks the scaffold: Python, Bash, and
PowerShell syntax, generation/replacement safety, Git preservation, version
selection, setup recovery, and commit hooks. Workflow commands are parsed with
their corresponding shell; PowerShell checks run on Windows CI, Bash checks on
macOS (and anywhere Bash is installed). Native Batch launchers are exercised by
the Windows tests. Install the validation dependency first:

```sh
python3 -m pip install -r .github/requirements.txt
```

Generated projects receive a separate `.github/workflows/validate.yml` that runs
their setup, build, and library tests. It does not run scaffold tests or require
Python validation packages. The render-time checks in
`.scaffold/scripts/scaffold/verify-output.cmake` only check staging completeness and JSON
before replacing files; they do not replace either validation suite.

Git pre commit hooks run repository validation. Run it manually:

```sh
python3 .github/validate.py
python3 .github/validate.py --full
```

`--full` builds with real vcpkg/fmt, tests static and shared libraries, and checks installed consumers. It requires network access. Commits to `main` run the full suite and block on failure; other branches run fast checks and allow commits with warnings.
