#!/bin/bash

# Open PRs for slackbuilds submitted via the form on the slackbuilds.org website.

set -e
set -o pipefail

if ! command -v go-github-apps > /dev/null 2>&1 ; then
  printf 'This scripts needs "go-github-apps". (https://github.com/nabeken/go-github-apps)\n'
  exit 1
fi

if ! command -v gh > /dev/null 2>&1 ; then
  printf 'This scripts needs "gh". (https://github.com/cli/cli)\n'
  exit 1
fi

BOT_NAME="sbo-bot[bot]"
BOT_ID="143931017"

GIT_REPO=SlackBuildsOrg/slackbuilds

APP_INSTALLATION_ID=41634818

ORIGPWD="$(pwd)"
CWD="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

TMP_FOLDER="$(mktemp -d)"
trap 'cd "$ORIGPWD" && rm -rf "$TMP_FOLDER"' INT TERM HUP QUIT EXIT

# shellcheck source=/dev/null
GITHUB_TOKEN="$(source "$CWD/../.env" && GITHUB_PRIV_KEY="$(echo -e "$PRIVATE_KEY")" go-github-apps -app-id "$APP_ID" -inst-id "$APP_INSTALLATION_ID")"
export GITHUB_TOKEN

printf 'Syncing data...\n'

(
  cd "$TMP_FOLDER"
  rsync -avPSH slackbuilds.org:/slackbuilds/www/pending/ pending

  gh repo clone "https://github.com/$GIT_REPO.git" slackbuilds -- --depth=1

  cd slackbuilds
  git config --local commit.gpgsign false
  git config --local user.name "$BOT_NAME"
  git config --local user.email "$BOT_ID+$BOT_NAME@users.noreply.github.com"
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

    found="$(find "$TMP_FOLDER/slackbuilds" -type d -name "$package" -maxdepth 2 -mindepth 2 \! -path '*/.git/*')"

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
      git push --set-upstream "https://$BOT_NAME:$GITHUB_TOKEN@github.com/$GIT_REPO.git" HEAD
      gh pr create --repo="$GIT_REPO" --head "$package-$checksum" --label submission-form --fill-first
    )

    ssh -n slackbuilds.org "mv www/pending/$package.tar* ~/ARCHIVE/"

    (
      cd "$TMP_FOLDER/slackbuilds"
      pr_number="$(gh pr list --repo="$GIT_REPO" --head "$package-$checksum" --json number --jq '.[].number')"

      printf 'Successfully created a PR for %s with number %s\n' "$category/$dir" "$number"

      printf "Would you like to schedule a build for %s: " "$category/$dir"

      read -u 3 -r answer

      if [ "$answer" = "y" ] || [ "$answer" = "yes" ] ; then
        printf "I'll output the PR diff now. Please inspect it *carefully*:\n"

        gh pr diff --repo="$GIT_REPO" "$pr_number"

        printf "Really queue builds %s? "

        read -u 3 -r answer

        if [ "$answer" = "y" ] || [ "$answer" = "yes" ] ; then
          gh pr comment --repo="$GIT_REPO" "$pr_number" --body "@sbo-bot: build $category/$dir"
        fi
      fi
    )
  done
} 3<&0
