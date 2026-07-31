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

if ! command -v glab > /dev/null 2>&1 ; then
  >&2 printf "This script depends on glab, install it and try again.\n"
  exit 1
fi

wait_for_pipeline() {
  local mr="$1"

  printf "Waiting for pipeline"

  while true; do
    local status

    status=$(glab mr view "$mr" --web=false --output=json | jq -r '.head_pipeline.status // "none"')

    case "$status" in
      success)
        printf "\nPipeline passed.\n"
        return 0
        ;;
      failed|canceled)
        printf "\nPipeline %s, aborting.\n" "$status"
        return 1
        ;;
      none)
        printf "\nNo pipeline found, aborting.\n"
        return 1
        ;;
      *)
        printf "."
        sleep 10
        ;;
    esac
  done
}

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
glab mr note create "$mr" -m "LGTM" --resolvable

mr_json=$(glab mr view "$mr" --web=false --output=json)
source_branch=$(echo "$mr_json" | jq -r .source_branch)
source_project_id=$(echo "$mr_json" | jq -r .source_project_id)
target_project_id=$(echo "$mr_json" | jq -r .target_project_id)

if [ "$source_project_id" = "$target_project_id" ]; then
  git push gitlab HEAD:"$source_branch" -f

  git push origin gitlab

  wait_for_pipeline "$mr"

  glab mr merge "$mr" --rebase --remove-source-branch --yes --auto-merge=false
else
  glab mr rebase "$mr"

  wait_for_pipeline "$mr"

  glab mr merge "$mr" --yes --auto-merge=false

  git push gitlab HEAD:gitlab -f

  git push origin gitlab
fi

git remote update --prune gitlab
