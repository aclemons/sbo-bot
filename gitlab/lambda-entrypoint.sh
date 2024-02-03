#!/bin/sh

set -e

# shellcheck source=/dev/null
. .venv/bin/activate

if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
  exec python3 sbobot/main.py
else
  python3 sbobot/fetch_env.py
  eval "$(sed 's/^/export /' /tmp/.env)"
  exec python3 sbobot/main.py
fi
