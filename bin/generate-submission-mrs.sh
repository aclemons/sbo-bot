#!/bin/bash

# Open MRs for slackbuilds submitted via the form on the slackbuilds.org website.

set -e
set -o pipefail

if ! command -v glab > /dev/null 2>&1 ; then
  printf 'This scripts needs "glab". (https://gitlab.com/gitlab-org/cli)\n'
  exit 1
fi

GIT_REPO=SlackBuilds.org/slackbuilds

ORIGPWD="$(pwd)"

TMP_FOLDER="$(mktemp -d)"
trap 'cd "$ORIGPWD" && rm -rf "$TMP_FOLDER"' INT TERM HUP QUIT EXIT

if [ -z "$GITLAB_TOKEN" ] ; then
  # shellcheck source=/dev/null
  GITLAB_TOKEN="$(source "$ORIGPWD/.env" && printf '%s\n' "$GITLAB_TOKEN")"
fi

if [ -z "$GITLAB_TOKEN" ] ; then
  printf 'This scripts needs a token for gitlab in the env "GITLAB_TOKEN".\n'
  exit 2
fi

export GITLAB_TOKEN

printf 'Syncing data...\n'

(
  cd "$TMP_FOLDER"
  rsync -avPSH slackbuilds.org:/slackbuilds/www/pending/ pending

  glab repo clone "https://gitlab.com/$GIT_REPO.git" slackbuilds -- --filter=tree:0

  cd slackbuilds
  git config --local commit.gpgsign false
)

{
   find "$TMP_FOLDER/pending" -name '*.tar*' -type f -maxdepth 1 -printf '%T@ %p\0' | sort -zk 1n | sed -z 's/^[^ ]* //' | xargs -0 -I xx basename xx | sed 's/\.tar.*$//' | while read -r package ; do
    printf "Checking submission %s\n" "$package"

    checksum="$(md5sum "$TMP_FOLDER/pending"/"$package".tar* | awk '{ print $1 }')"

    (
      cd "$TMP_FOLDER/slackbuilds/"
      git checkout master
      git reset --hard origin/master
      git checkout -b "$package-$checksum"
    )

    found="$(find "$TMP_FOLDER/slackbuilds" -type d -name "$package" \! -path '*/.git/*')"

    if [ "" = "$found" ] ; then
      printf 'New submission found %s\n' "$package"

      printf 'Please find the submission email and enter the category: '
      read -u 3 -r category
      printf 'Now please enter the short description for the commit message. Only the part which will appear between the brackets: '
      read -u 3 -r msg

      dir="$package"

      (
        cd "$TMP_FOLDER/slackbuilds/$category"
        rm -rf "$dir"
        tar -xf "$TMP_FOLDER/pending"/"$package".tar*
        cd "$dir"
        chmod 0644 -- *SlackBuild

        # shellcheck source=/dev/null
        . "$dir".info

        git add .
        git commit --author "$MAINTAINER <$EMAIL>" -m "$category/$PRGNAM: Added ($msg)." --no-verify
      )
    else
      printf 'Update for an existing script found %s => %s\n' "$package" "$found"

      dir="$(basename "$found")"
      category="$(basename "$(dirname "$found")")"

      (
        cd "$TMP_FOLDER/slackbuilds/$category"
        cd "$dir"
        # shellcheck source=/dev/null
        . "$dir".info
        cd ..
        OLD_VERSION="$VERSION"

        rm -rf "$dir"
        tar -xf "$TMP_FOLDER/pending"/"$package".tar*
        cd "$dir"
        chmod 0644 -- *SlackBuild

        # shellcheck source=/dev/null
        . "$dir".info

        git add .
        if [ "$VERSION" = "$OLD_VERSION" ] ; then
          printf 'Looks like the version did not change. Please enter the commit message: '
          read -u 3 -r msg
          git commit --author "$MAINTAINER <$EMAIL>" -m "$category/$PRGNAM: $msg." --no-verify
        else
          git commit --author "$MAINTAINER <$EMAIL>" -m "$category/$PRGNAM: Updated for version $VERSION." --no-verify
        fi
      )
    fi

    (
      cd "$TMP_FOLDER/slackbuilds"
      git push --set-upstream "https://gitlab-ci-token:$GITLAB_TOKEN@gitlab.com/$GIT_REPO.git" HEAD
      GITLAB_TOKEN="$GITLAB_TOKEN" glab mr create --source-branch "$package-$checksum" --repo="$GIT_REPO" --label submission-form --fill --yes
    )
  done
} 3<&0
