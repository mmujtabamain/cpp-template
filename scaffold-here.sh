#!/bin/sh

set -eu

# use the repository root even when called from another directory
repository_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$repository_root/.scaffold/scaffold.sh" "$repository_root" "$@"
