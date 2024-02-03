#!/bin/sh

set -e

# shellcheck source=/dev/null
. .venv/bin/activate

exec python3 sbobot/main.py
