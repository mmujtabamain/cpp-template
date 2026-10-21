#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# execute setup.cmake from project root
exec cmake "-DDEV_PRESET=${1:-debug}" -P "$project_root/scripts/setup.cmake"
