#!/bin/sh

set -e

printf 'Fetching env configuration from ssm\n'
python3 -m sbobot.fetch_env
eval "$(sed 's/^/export /' /tmp/.env)"
exec python3 -m sbobot.main
