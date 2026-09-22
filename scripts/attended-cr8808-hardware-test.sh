#!/bin/sh
# Explicitly attended; default is preflight only.
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
exec python3 "$root/scripts/hardware_test.py" "$@"
