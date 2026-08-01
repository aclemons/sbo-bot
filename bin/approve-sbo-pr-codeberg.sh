#!/bin/bash

set -e
set -o pipefail

print_help() {
  printf "Usage: %s <prid>\n" "$0"
  printf "Approve a pull request in the SlackBuilds.org Codeberg organisation:\n"
  printf "  Make sure the working directory is your clone and that you have two remotes: origin and codeberg:\n"
  printf "Arguments:\n"
  printf "  <prid>   The id of the PR to approve.\n"
  printf "Options:\n"
  printf "  -h, --help   Print this help message.\n"
}

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  print_help
  exit 0
fi

if ! command -v fj > /dev/null 2>&1 ; then
  >&2 printf "This script depends on forgejo-cli, install it and try again.\n"
  exit 1
fi

pr="$1"

if [ -z "$pr" ] ; then
  print_help
  exit 1
fi

fj -H codeberg.org pr view "$pr" diff | bat --paging=always
fj -H codeberg.org pr view "$pr" comments

read -r approve

if [ "$approve" != "y" ] ; then
  exit 0
fi

CODEBERG_TOKEN="$(jq -r '.hosts."codeberg.org".token' ~/.local/share/forgejo-cli/keys.json)"

current_user="$(curl -f -s "https://codeberg.org/api/v1/user" \
     -H "Authorization: token $CODEBERG_TOKEN" | jq -r .login)"
pr_author="$(curl -f -s "https://codeberg.org/api/v1/repos/SlackBuildsOrg/slackbuilds/pulls/$pr" \
     -H "Authorization: token $CODEBERG_TOKEN" | jq -r .user.login)"

fj -H codeberg.org pr view "$pr" diff --patch | git am -s
git commit --amend

curl -f -s -X PATCH "https://codeberg.org/api/v1/repos/SlackBuildsOrg/slackbuilds/pulls/$pr" \
     -H "Authorization: token $CODEBERG_TOKEN" \
     --json '{"base":"codeberg"}' | jq -r .updated_at

if [ "$pr_author" = "$current_user" ] ; then
  curl -f -s "https://codeberg.org/api/v1/repos/SlackBuildsOrg/slackbuilds/issues/$pr/comments" \
       -H "Authorization: token $CODEBERG_TOKEN" \
       --json '{"body": "LGTM"}' | jq -r .updated_at
else
  curl -f -s "https://codeberg.org/api/v1/repos/SlackBuildsOrg/slackbuilds/pulls/$pr/reviews" \
       -H "Authorization: token $CODEBERG_TOKEN" \
       --json '{"body": "LGTM", "event": "approve"}' | jq
fi

git push origin && git push codeberg

sha="$(git rev-parse HEAD)"
curl -f -s "https://codeberg.org/api/v1/repos/SlackBuildsOrg/slackbuilds/pulls/$pr/merge" \
     -H "Authorization: token $CODEBERG_TOKEN" \
     --json '{"Do": "manually-merged", "MergeCommitID": "'"$sha"'","delete_branch_after_merge":true}'
