#!/bin/sh
# Collect native input; shared CMake code owns validation and generation.
# Stop on failed commands or unset variables.
set -eu
# Locate the template even when invoked from another directory.
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -gt 3 ]; then
    echo "Usage: $0 [project-name] [exec|library] [--force]" >&2
    exit 1
fi
# Arguments support automation; prompt only for missing values.
name=${1-}
type=${2-}
if [ -z "$name" ]; then printf 'Project name: '; IFS= read -r name; fi
if [ -z "$type" ]; then printf 'Project type [exec/library]: '; IFS= read -r type; fi
# Destructive replacement still prompts unless --force is explicit.
force=OFF
if [ "${3-}" = '--force' ]; then force=ON
elif [ -n "${3-}" ]; then echo "Expected --force as third argument" >&2; exit 1; fi
# Replace this process so the CMake exit status reaches the caller.
exec cmake "-DPROJECT_DISPLAY_NAME=$name" "-DPROJECT_TYPE=$type" "-DSCAFFOLD_FORCE=$force" -P "$root/.template/scripts/scaffold.cmake"
