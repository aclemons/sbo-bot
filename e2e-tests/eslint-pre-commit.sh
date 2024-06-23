#!/usr/bin/env bash

set -e
set -o pipefail

CWD="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

(
  cd "$CWD"

  ARGS=()
  for arg in "$@"
  do
    ARGS+=( "${arg#"e2e-tests/"}" )
  done

  npm run lint-fix-pre-commit "${ARGS[*]}"
)
