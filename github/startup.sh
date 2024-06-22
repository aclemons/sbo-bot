#!/bin/sh

set -e

printf 'Fetching env configuration from ssm\n'
node lib/fetch_env.js
eval "$(sed 's/^/export /' /tmp/.env)"
exec node_modules/.bin/probot run /usr/src/app/lib/index.js "$@"
