#!/bin/sh

set -eu

if [ "$#" -lt 1 ] || [ -z "$1" ]; then
    echo "Usage: $0 <location> [project-name] [exec|library] [--force] [--no-git]" >&2
    exit 1
fi

# calculate root first; args are shifted later
scaffold_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# * ARGUMENTS START * ----------------------------------------------- #

# get destination
scaffold_destination=$1
shift

# get project name
project_name=${1-}

# if another arg present; get project type
if [ "$#" -gt 0 ]; then shift; fi 
project_type=${1-}

# if another arg present; get --force and --no-git flags
if [ "$#" -gt 0 ]; then shift; fi
force_replacement=OFF
generate_git=ON
for argument in "$@"; do
    case "$argument" in
        --force) force_replacement=ON ;;
        --no-git) generate_git=OFF ;;
        *) echo "Unknown scaffold option: $argument" >&2; exit 1 ;; # exit on invalid argument
    esac
done

# if not in args; get project name
if [ -z "$project_name" ]; then
    printf 'Project name: '
    IFS= read -r project_name
fi

# if not in args; get project type
if [ -z "$project_type" ]; then
    printf 'Project type [exec|library]: '
    IFS= read -r project_type
fi

# * ARGUMENTS END * ------------------------------------------------- #

exec cmake \
    "-DSCAFFOLD_DESTINATION=$scaffold_destination" \
    "-DPROJECT_DISPLAY_NAME=$project_name" \
    "-DPROJECT_TYPE=$project_type" \
    "-DSCAFFOLD_FORCE=$force_replacement" \
    "-DSCAFFOLD_GIT=$generate_git" \
    -P "$scaffold_root/scripts/scaffold.cmake"
