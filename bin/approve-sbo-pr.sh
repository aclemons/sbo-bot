#!/bin/bash

set -e
set -o pipefail

print_help() {
  printf "Usage: %s <prid>\n" "$0"
  printf "Approve an pull request in the SlackBuilds.org GitHub organisation:\n"
  printf "  Make sure the working directory is your clone and that you have two remotes: origin and github:\n"
  printf "Arguments:\n"
  printf "  <prid>   The id of the PR to approve.\n"
  printf "Options:\n"
  printf "  -h, --help   Print this help message.\n"
}

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  print_help
  exit 0
fi

if ! command -v gh > /dev/null 2>&1 ; then
  >&2 printf "This script depends on gh-cli, install it and try again.\n"
  exit 1
fi

pr="$1"

if [ -z "$pr" ] ; then
  print_help
  exit 1
fi

gh pr diff "$pr"
gh pr view --comments "$pr"

read -r approve

if [ "$approve" != "y" ] ; then
   exit 0
fi

gh pr diff "$pr" --patch | git am -s
git commit --amend

gh pr edit "$pr" --base github
gh pr review "$pr" -a -b "LGTM"

git push origin && git push github
gh pr merge --rebase "$pr"
