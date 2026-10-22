#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

development_preset=debug
clean_setup=OFF
for argument in "$@"; do
    case "$argument" in
        --clean) clean_setup=ON ;;
        debug|release) development_preset=$argument ;;
        *) echo "Usage: $0 [debug|release] [--clean]" >&2; exit 1 ;;
    esac
done

# execute setup.cmake from project root
exec cmake "-DSETUP_CLEAN=$clean_setup" "-DDEV_PRESET=$development_preset" -P "$project_root/scripts/setup.cmake"
