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
display name and `exec` or `library`. For example, `Vector Math` becomes the
CMake/package target `VectorMath`, namespace/header directory `vector_math`,
and vcpkg manifest name `vector-math`.

For automation:

```sh
./scaffold.sh "Vector Math" library
# Explicit destructive recovery, without an interactive prompt:
./scaffold.sh "Vector Math" library --force
```

Batch accepts the same arguments. You can also call CMake directly:

```sh
cmake "-DPROJECT_DISPLAY_NAME=Vector Math" -DPROJECT_TYPE=library -P .template/scripts/scaffold.cmake
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

Template sources and validation live under `.template/`. Run validation with:

```sh
python3 .template/tests/validate.py
python3 .template/tests/validate.py --integration
```

The integration mode uses real upstream vcpkg and fmt and requires network
access. GitHub Actions runs it on macOS and Windows, including installed static
and shared library consumers. Scaffold-only validation requires just Python
and CMake.
