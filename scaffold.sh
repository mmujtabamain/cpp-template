#!/bin/sh
# Collect native input; shared CMake code owns validation and generation.
# Stop on failed commands or unset variables.
set -eu

# Locate the template even when invoked from another directory.
repository_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ "$#" -gt 3 ]; then
    echo "Usage: $0 [project-name] [exec|library] [--force]" >&2
    exit 1
fi

# Arguments support automation; prompt only for missing values.
project_name=${1-}
project_type=${2-}

if [ -z "$project_name" ]; then
    printf 'Project name: '
    IFS= read -r project_name
fi

if [ -z "$project_type" ]; then
    printf 'Project type [exec/library]: '
    IFS= read -r project_type
fi

# Destructive replacement still prompts unless --force is explicit.
force_replacement=OFF

if [ "${3-}" = '--force' ]; then
    force_replacement=ON
elif [ -n "${3-}" ]; then
    echo "Expected --force as third argument" >&2
    exit 1
fi

# Replace this process so the CMake exit status reaches the caller.
exec cmake \
    "-DPROJECT_DISPLAY_NAME=$project_name" \
    "-DPROJECT_TYPE=$project_type" \
    "-DSCAFFOLD_FORCE=$force_replacement" \
    -P "$repository_root/.template/scripts/scaffold.cmake"
