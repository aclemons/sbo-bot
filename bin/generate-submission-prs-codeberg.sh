#!/bin/bash

# Open PRs for slackbuilds submitted via the form on the slackbuilds.org website.

set -e
set -o pipefail

if ! command -v fj > /dev/null 2>&1 ; then
  printf 'This scripts needs "fj". (https://codeberg.org/forgejo-contrib/forgejo-cli)\n'
  exit 1
fi

GIT_REPO=SlackBuildsOrg/slackbuilds

ORIGPWD="$(pwd)"

TMP_FOLDER="$(mktemp -d)"
trap 'cd "$ORIGPWD" && rm -rf "$TMP_FOLDER"' INT TERM HUP QUIT EXIT

printf 'Syncing data...\n'

(
  cd "$TMP_FOLDER"
  rsync -avPSH slackbuilds.org:/slackbuilds/www/pending/ pending

  # fj cannot pass git options such as --depth, so clone directly with git
  # over SSH for now.
  git clone --depth=1 "git@codeberg.org:$GIT_REPO.git" slackbuilds

  cd slackbuilds
  git config --local commit.gpgsign false
)

{
   find "$TMP_FOLDER/pending" -name '*.tar*' -type f -maxdepth 1 -printf '%T@ %p\0' | sort -zk 1n | sed -z 's/^[^ ]* //' | xargs -0 -I xx basename xx | sed 's/\.tar.*$//' | while read -r package ; do
    printf "Checking submission %s\n" "$package"

    printf 'Details:\n\n'
    ssh -n slackbuilds.org /slackbuilds/bin/sbodb -S "$package" || true
    printf '\n\n'

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

      printf 'Please enter the category from the submission email: '
      read -u 3 -r category
      printf 'Now please enter the short description for the commit message. Only the part which will appear between the brackets: '
      read -u 3 -r msg
      printf "Please enter the maintainer's name from the submission email: "
      read -u 3 -r maintainer
      printf 'Please enter the actual email in the New upload line from the submission email: '
      read -u 3 -r email

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
        GIT_AUTHOR_NAME="$maintainer" GIT_AUTHOR_EMAIL="$email" git commit -m "$category/$PRGNAM: Added ($msg)." --no-verify
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

        printf "Please enter the maintainer's name from the submission email: "
        read -u 3 -r maintainer
        printf 'Please enter the actual email in the New upload line from the submission email: '
        read -u 3 -r email

        if [ "$VERSION" = "$OLD_VERSION" ] ; then
          printf 'Looks like the version did not change. Please enter the commit message: '
          read -u 3 -r msg
          GIT_AUTHOR_NAME="$maintainer" GIT_AUTHOR_EMAIL="$email" git commit -m "$category/$PRGNAM: $msg." --no-verify
        else
          GIT_AUTHOR_NAME="$maintainer" GIT_AUTHOR_EMAIL="$email" git commit -m "$category/$PRGNAM: Updated for version $VERSION." --no-verify
        fi
      )
    fi

    (
      cd "$TMP_FOLDER/slackbuilds"
      # fj has no push command, so fall back to git over SSH.
      git push --set-upstream origin HEAD

      # fj pr create does not support labels, so add it afterwards.
      pr_output="$(fj -H codeberg.org pr create --repo="$GIT_REPO" --base master --head "$package-$checksum" --autofill)"
      printf '%s\n' "$pr_output"

      pr_number="$(printf '%s' "$pr_output" | grep -oE 'pulls/[0-9]+' | grep -oE '[0-9]+' | head -n1 || true)"
      if [ -n "$pr_number" ] ; then
        fj -H codeberg.org pr edit "$pr_number" labels -a submission-form \
          || printf 'Could not add the submission-form label. Please add it to PR %s manually.\n' "$pr_number"

        printf 'Successfully created a PR for %s with number %s\n' "$category/$dir" "$pr_number"

        printf "Would you like to schedule a build for %s: " "$category/$dir"

        read -u 3 -r answer

        if [ "$answer" = "y" ] || [ "$answer" = "yes" ] ; then
          printf "I'll output the PR diff now. Please inspect it *carefully*:\n"

          fj -H codeberg.org pr view "$pr_number" diff

          printf "Really queue builds? "

          read -u 3 -r answer

          if [ "$answer" = "y" ] || [ "$answer" = "yes" ] ; then
            fj -H codeberg.org pr comment "$pr_number" "@sbo-bot: build $category/$dir"
          fi
        fi
      else
        printf 'Could not determine the PR number. Please add the submission-form label manually.\n'
      fi
    )

    ssh -n slackbuilds@slackbuilds.org "mv ~/www/pending/$package.tar* ~/ARCHIVE/"
  done
} 3<&0
