# cpp-template

Generate an executable or an installable static/shared C++23 library from this repository template.

| OS      | Support           | Build CI |
| ------- | ----------------- | -------- |
| Windows | Supported         | ✅       |
| macOS   | Supported         | ✅       |
| Linux   | Not yet validated | -        |

# Prerequisites

CMake 3.24+, Ninja, Git, Python 3 for Git hooks, and a C++23 compiler (Xcode command line tools on macOS; Visual Studio C++ tools and a Developer Command Prompt on Windows; GCC or Clang on Linux).

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

### Enable Hooks see [Git hooks](#commit-validation)

Enable the tracked hooks once in each template clone:

```sh
python3 .github/install-hooks.py
```

The installer sets the clone's local `core.hooksPath` to `.github/hooks`; it leaves an existing custom local hook path unchanged.

> Hooks prefer Python from `.venv/`, then fall back to Python on `PATH`.

### Run setup script

Run `setup.sh` afterwards to complete the setup. Normal setup reuses dependencies
and build output. To recover from a failed clone/bootstrap, run `./setup.sh --clean`
(or `setup.bat --clean`). **Warning:** clean setup deletes `external/vcpkg/`,
`vcpkg_installed/`, and `build/`, including local changes, then clones and sets up
again. Project source files and the project's Git metadata are preserved.

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

## Commit validation

Git pre commit hooks run `validate.py`. Run it manually to see the checks and warnings:

```sh
python3 .github/validate.py
python3 .github/validate.py --full
```

`--full` builds with real vcpkg/fmt, tests static and shared libraries, and checks installed consumers. It requires network access. Commits to `main` run the full suite and block on failure; other branches run fast checks and allow commits with warnings.
