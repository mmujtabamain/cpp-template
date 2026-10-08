#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -gt 3 ]; then
    echo "Usage: $0 [project-name] [exec|library] [--force]" >&2
    exit 1
fi
name=${1-}
type=${2-}
if [ -z "$name" ]; then printf 'Project name: '; IFS= read -r name; fi
if [ -z "$type" ]; then printf 'Project type [exec/library]: '; IFS= read -r type; fi
force=OFF
if [ "${3-}" = '--force' ]; then force=ON
elif [ -n "${3-}" ]; then echo "Expected --force as third argument" >&2; exit 1; fi
exec cmake "-DPROJECT_DISPLAY_NAME=$name" "-DPROJECT_TYPE=$type" "-DSCAFFOLD_FORCE=$force" -P "$root/.template/scripts/scaffold.cmake"
