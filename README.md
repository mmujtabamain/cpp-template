# cpp-template

Generate an executable or an installable static/shared C++23 library from this repository template.

> # table showing OS support, check windows, mac and linux

Prerequisites: CMake 3.24+, Ninja, Git, and a C++23 compiler (Xcode command line tools on macOS; Visual Studio C++ tools and a Developer Command Prompt on Windows).

> # commands to setup pre reqs

# Setup

> On Windows use `*.bat`

Run `scaffold.sh` script with name and type, type can `exec` or `library`. `exec` for executable programs and `library` for libraries. Use `--force` to overwrite existing contents if present.

```sh
./scaffold.sh "Sample Project" exec
```

> Names must start with an ASCII letter and use letters, digits, spaces, underscores or hyphens; reserved identifiers are rejected. Name in other notations derived automatically, i.e `sample-project`, `SampleProject` etc.

You can also call CMake directly:

```sh
cmake "-DPROJECT_DISPLAY_NAME=Sample Library" -DPROJECT_TYPE=library -P .template/scripts/scaffold.cmake
```

After scaffolding, you **HAVE** to remove template files manually.

Run `setup.sh` afterwards to complete the setup.

## Commit and merge validation

Enable the tracked hooks once in each clone:

```sh
python3 .github/install-hooks.py
```

The installer sets the clone's local `core.hooksPath` to `.github/hooks`; it leaves an existing custom local hook path alone.
> Hooks prefer Python from `.venv/`, then fall back to Python on `PATH`.
