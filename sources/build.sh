#!/bin/sh
# Install requirements-source.txt first; compile UFO edits without regenerating them.
set -eu
exec python "$(dirname "$0")/build.py" "$@"
