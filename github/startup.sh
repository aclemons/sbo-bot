#!/bin/sh

set -e

if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
  exec node_modules/.bin/probot run /usr/src/app/lib/index.js "$@"
else
  printf 'Fetching env configuration from ssm\n'
  node lib/fetch_env.js
  eval "$(sed 's/^/export /' /tmp/.env)"
  exec node_modules/.bin/probot run /usr/src/app/lib/index.js "$@"
fi
