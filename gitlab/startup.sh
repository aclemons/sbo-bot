#!/bin/sh

set -e

cd /usr/src/app/

# shellcheck source=/dev/null
. .venv/bin/activate

printf 'Fetching env configuration from ssm\n'
python3 sbobot/fetch_env.py
eval "$(sed 's/^/export /' /tmp/.env)"
exec python3 sbobot/main.py
