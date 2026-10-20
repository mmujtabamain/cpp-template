#!/bin/sh

set -eu

if [ "$#" -gt 3 ]; then
    echo "Usage: $0 [project-name] [exec|library] [--force]" >&2
    exit 1
fi

# * ARGUMENTS START * ----------------------------------------------- #

# capture exact user input 
project_name=${1-}
if [ -z "$project_name" ]; then
    printf 'Project name: '
    IFS= read -r project_name
fi

# capture exact user input 
project_type=${2-}
if [ -z "$project_type" ]; then
    printf 'Project type [exec/library]: '
    IFS= read -r project_type
fi

# make sure third arg is --force or nothing as third argument
force_replacement=OFF
if [ "${3-}" = '--force' ]; then
    force_replacement=ON
elif [ -n "${3-}" ]; then
    echo "Expected --force as third argument" >&2
    exit 1
fi

# * ARGUMENTS END * ------------------------------------------------- #

# Replace this process so the CMake exit status reaches the caller.
repository_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec cmake \
    "-DPROJECT_DISPLAY_NAME=$project_name" \
    "-DPROJECT_TYPE=$project_type" \
    "-DSCAFFOLD_FORCE=$force_replacement" \
    -P "$repository_root/.template/scripts/scaffold.cmake"
