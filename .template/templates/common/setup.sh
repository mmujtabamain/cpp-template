#!/bin/sh
# Prepare dependencies and configure the development environment; implementation lives in scripts/setup.cmake.
set -eu
# Locate the generated project independently of the caller's working directory.
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# The optional first argument selects a preset; debug is the default.
# exec propagates failures directly to the calling shell.
exec cmake "-DDEV_PRESET=${1:-debug}" -P "$root/scripts/setup.cmake"
