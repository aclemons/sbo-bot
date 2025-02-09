#!/bin/bash

set -e
set -o pipefail

VERSION="$(curl -f -s https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Lambda-Insights-extension-versionsx86-64.html | sed -n '/<h2/,$p' | sed -n 1p | sed 's/^.*">\(.*\)<\/.*$/\1/')"

find . -name  'Dockerfile' -exec sed -i "s/^\(ENV EXTENSION_VERSION=\).*$/\1$VERSION/" {} \;

if [[ $(git status --porcelain) ]]; then
  curl -f -s -o /tmp/amd64 "https://lambda-insights-extension.s3-eu-central-1.amazonaws.com/amazon_linux/lambda-insights-extension.$VERSION.rpm"
  SUMAMD64="$(sha512sum /tmp/amd64 | awk '{ print $1 }')"
  find . -name  'Dockerfile' -exec sed -i "s/^\(ENV EXTENSION_CHECKSUM_AMD64=\).*$/\1$SUMAMD64/" {} \;

  curl -f -s -o /tmp/arm64 "https://lambda-insights-extension-arm64.s3-eu-central-1.amazonaws.com/amazon_linux/lambda-insights-extension-arm64.$VERSION.rpm"
  SUMARM64="$(sha512sum /tmp/arm64 | awk '{ print $1 }')"
  find . -name  'Dockerfile' -exec sed -i "s/^\(ENV EXTENSION_CHECKSUM_ARM64=\).*$/\1$SUMARM64/" {} \;
fi

if [ -n "$GITHUB_ENV" ] ; then
  printf 'EXTENSION_VERSION=%s\n' "$VERSION" >> "$GITHUB_ENV"
fi
