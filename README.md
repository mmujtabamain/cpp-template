# cpp-template

Generate an executable or an installable static/shared C++23 library from this repository template.

| OS      | Support           | Build CI |
| ------- | ----------------- | -------- |
| Windows | Supported         | ✅       |
| macOS   | Supported         | ✅       |
| Linux   | Not yet validated | —        |

# Prerequisites

CMake 3.24+, Ninja, Git, Python 3 for Git hooks, and a C++23 compiler (Xcode command line tools on macOS; Visual Studio C++ tools and a Developer Command Prompt on Windows; GCC or Clang on Linux).

**macOS** - with [Homebrew](https://brew.sh/) installed:

```sh
xcode-select --install
brew install cmake ninja git python pkgconf
```

**Windows** — with [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/) installed:

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

Run `scaffold.sh` with a project name and type: `exec` for executable programs or `library` for libraries. Use `--force` to overwrite an existing generated project without confirmation.

```sh
./scaffold.sh "Sample Project" exec
```

> Names must start with an ASCII letter and contain only letters, digits, spaces, underscores, or hyphens; reserved identifiers are rejected. Other naming forms, such as `sample-project`, `SampleProject`, and `sample_project`, are derived automatically.

After scaffolding, you **MUST** manually remove `.template/`, `scaffold.sh`, and `scaffold.bat`.

Run `setup.sh` afterwards to complete the setup.

## Commit and merge validation

Enable the tracked hooks once in each clone:

```sh
python3 .github/install-hooks.py
```

The installer sets the clone's local `core.hooksPath` to `.github/hooks`; it leaves an existing custom local hook path unchanged.

> Hooks prefer Python from `.venv/`, then fall back to Python on `PATH`.
