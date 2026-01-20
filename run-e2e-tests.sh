#!/usr/bin/env bash

set -e

CWD="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

(
  cd "$CWD"

  docker compose down --remove-orphans
  docker compose up -d --wait --quiet-pull --remove-orphans moto

  "$CWD/seed.sh"

  docker compose up -d --wait --quiet-pull --remove-orphans --build
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
