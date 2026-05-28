#!/bin/bash

set -e
set -o pipefail

print_help() {
  printf "Usage: %s <prid>\n" "$0"
  printf "Approve an pull request in the SlackBuilds.org Gitlab organisation:\n"
  printf "  Make sure the working directory is your clone and that you have two remotes: origin and gitlab:\n"
  printf "Arguments:\n"
  printf "  <prid>   The id of the PR to approve.\n"
  printf "Options:\n"
  printf "  -h, --help   Print this help message.\n"
}

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  print_help
  exit 0
fi

if ! command -v glab ; then
  >&2 printf "This script depends on glab, install it and try again.\n"
  exit 1
fi

mr="$1"

if [ -z "$mr" ] ; then
  print_help
  exit 1
fi

glab mr diff "$mr"
glab mr view "$mr" --comments

read -r approve
if [ "$approve" != "y" ] ; then
   exit 0
fi

wget -q -O- "https://gitlab.com/SlackBuilds.org/slackbuilds/-/merge_requests/$mr.patch" | git am -s --no-verify
git commit --amend --no-verify

glab mr update "$mr" --target-branch gitlab

glab mr approve "$mr"
glab mr note "$mr" -m "LGTM"

source_branch=$(glab mr view "$mr" --web=false --output=json | jq -r .source_branch)
git push gitlab HEAD:"$source_branch" -f

git push origin gitlab

echo "Waiting for pipeline..."
sleep 45

glab mr merge "$mr" --rebase --remove-source-branch --yes --auto-merge=false

git remote update --prune gitlab
