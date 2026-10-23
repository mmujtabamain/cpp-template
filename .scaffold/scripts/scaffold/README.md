# Scaffold modules

`../scaffold.cmake` is the CLI entry point. It reads CLI variables, calls the
modules, and reports the result. Including a module only defines functions;
it does not validate input, render files, or replace a project.

Each module includes its own utility dependency. Functions receive all project
data as arguments and return values only through named output variables.
Temporary variables and template substitutions stay inside function scope.
No module requires another module to have run first.

| Module | Public function | Inputs and result |
| --- | --- | --- |
| `inputs.cmake` | `scaffold_validate_inputs` | Explicit destination, display name, type, Git-copy flag, versions, and scaffold root; returns a normalized request. |
| `identity.cmake` | `scaffold_project_identity` | Display name and output variable; returns normalized project identifiers. |
| `compatibility.cmake` | `scaffold_resolve_compatibility` | Manifest path, selected versions, and running CMake version; returns compatible version settings. |
| `render.cmake` | `scaffold_render_project` | Template and staging paths plus request, identity, and version values; writes staging only. |
| `verify-output.cmake` | `scaffold_verify_output` | Staging path, type, identifiers, Git-copy and preset flags; checks files and JSON without changing staging. |
| `replace.cmake` | `scaffold_replace_project` | Destination, staging path, force flag, and output variable; confirms and installs staging, returning `ON` for installation or `OFF` for cancellation. |
| `utils.cmake` | Shared helpers | Argument/path checks, JSON encoding, symlink-safe removal, and yes/no prompts. |

The request, identity, and version results are JSON value records. JSON preserves
strings across function boundaries without CMake list splitting. The record fields
are documented at their producing functions; consumers read only their explicit
record arguments. They can also receive records constructed by another caller.

For example, identity normalization can run by itself:

```cmake
cmake_minimum_required(VERSION 3.24)
include("/path/to/.scaffold/scripts/scaffold/identity.cmake")

scaffold_project_identity("Example Library" identity)
string(JSON target_name GET "${identity}" name)
message(STATUS "Target: ${target_name}")
```

The CLI coordinates validation before replacement. The replacement function
expects already verified staging; it also checks destructive path overlap before
removing generated files. Canceling replacement returns to the caller.

Repository validation includes independent import, repeated-call, caller-variable
isolation, read-only verification, and replacement tests in
`.github/scripts/tests/scaffold_module_tests.py`.
