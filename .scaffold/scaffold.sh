#!/bin/sh

set -eu

if [ "$#" -lt 1 ] || [ -z "$1" ]; then
    echo "Usage: $0 <location> [project-name] [exec|library] [--force] [--no-git]" >&2
    exit 1
fi

# * ARGUMENTS START * ----------------------------------------------- #

# capture the destination and exact user input
scaffold_destination=$1
shift
project_name=${1-}
if [ "$#" -gt 0 ]; then shift; fi
project_type=${1-}
if [ "$#" -gt 0 ]; then shift; fi

# optionally omit template Git files
force_replacement=OFF
generate_git=ON
for argument in "$@"; do
    case "$argument" in
        --force) force_replacement=ON ;;
        --no-git) generate_git=OFF ;;
        *) echo "Unknown scaffold option: $argument" >&2; exit 1 ;;
    esac
done

if [ -z "$project_name" ]; then
    printf 'Project name: '
    IFS= read -r project_name
fi

if [ -z "$project_type" ]; then
    printf 'Project type [exec/library]: '
    IFS= read -r project_type
fi

# * ARGUMENTS END * ------------------------------------------------- #

scaffold_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec cmake \
    "-DSCAFFOLD_DESTINATION=$scaffold_destination" \
    "-DPROJECT_DISPLAY_NAME=$project_name" \
    "-DPROJECT_TYPE=$project_type" \
    "-DSCAFFOLD_FORCE=$force_replacement" \
    "-DSCAFFOLD_GIT=$generate_git" \
    -P "$scaffold_root/scripts/scaffold.cmake"
