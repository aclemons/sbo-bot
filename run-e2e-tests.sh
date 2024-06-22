#!/bin/bash

set -e
set -o allexport

CWD="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

(
  cd "$CWD"

  docker compose down --remove-orphans
  docker compose up -d --wait --quiet-pull --remove-orphans
)

cleanup() {
  (
    cd "$CWD"

    docker compose down --remove-orphans
  )
}
trap "cleanup" INT TERM HUP QUIT EXIT

(
  cd "$CWD/e2e-tests/"
  npm ci
  npm run test
)
