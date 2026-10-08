#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec cmake "-DDEV_PRESET=${1:-debug}" -P "$root/scripts/run.cmake"
