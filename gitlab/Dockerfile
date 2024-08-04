# syntax=docker/dockerfile:1.9.0@sha256:fe40cf4e92cd0c467be2cfc30657a680ae2398318afd50b0c80585784c604f28

FROM aclemons/slackware:current@sha256:e1a1c974e251ed093f4a5cbf4f40d31f40d25272acf9034b3df2ad7cab2e9564 AS base

RUN export TERSE=0 && \
    sed -i '/^WGETFLAGS/s/"$/ -q"/' /etc/slackpkg/slackpkg.conf && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on install brotli ca-certificates cyrus-sasl curl dcron nghttp2 nghttp3 perl || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    c_rehash && update-ca-certificates && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current

# renovate: datasource=github-releases depName=aws/aws-lambda-runtime-interface-emulator
ARG AWS_LAMBDA_RIE_VERSION=v1.21

RUN if [ "$(uname -m)" = "aarch64" ] ; then curl -o /usr/local/bin/aws-lambda-rie -L "https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/download/$AWS_LAMBDA_RIE_VERSION/aws-lambda-rie-arm64" ; else curl -o /usr/local/bin/aws-lambda-rie -L "https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/download/$AWS_LAMBDA_RIE_VERSION/aws-lambda-rie-x86_64" ; fi && \
    chown root:root /usr/local/bin/aws-lambda-rie && chmod 0755 /usr/local/bin/aws-lambda-rie


FROM base AS lambda-layers

ENV EXTENSION_VERSION=1.0.317.0
ENV EXTENSION_CHECKSUM_ARM64=8f3aeea6f69bffba52d6e47ddc05a8b967cfb7970a17596d3d7187f684dcbf498d22a2fec3b10c724408ea43b9f395f84510a2da93571ac1074ed96db82899a9
ENV EXTENSION_CHECKSUM_AMD64=cc8d2ae5717c23975ef8cfd3e049e20280aaa3493a06e57a297cf97fd7e1d7ca6501d1d6243cb24e89e5595f701aefe1415fcbec077758d2febe4677faccb374

WORKDIR /
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN export TERSE=0 && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on install cpio icu4c libgcrypt libgpg-error lua patchelf rpm sqlite || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current && \
    rm /root/.gnupg/public-keys.d/pubring.db.lock && \
    if [ "$(uname -m)" = "x86_64" ] ; then curl -o /tmp/lambda-insights-extension.rpm -L "https://lambda-insights-extension.s3-ap-northeast-1.amazonaws.com/amazon_linux/lambda-insights-extension.$EXTENSION_VERSION.rpm" ; fi && \
    if [ "$(uname -m)" = "x86_64" ] ; then echo "$EXTENSION_CHECKSUM_AMD64 /tmp/lambda-insights-extension.rpm" | sha512sum --strict --check ; fi && \
    if [ "$(uname -m)" = "aarch64" ] ; then curl -o /tmp/lambda-insights-extension.rpm -L "https://lambda-insights-extension-arm64.s3-ap-northeast-1.amazonaws.com/amazon_linux/lambda-insights-extension-arm64.$EXTENSION_VERSION.rpm" ; fi && \
    if [ "$(uname -m)" = "aarch64" ] ; then echo "$EXTENSION_CHECKSUM_ARM64 /tmp/lambda-insights-extension.rpm" | sha512sum --strict --check ; fi && \
    rpm2cpio < /tmp/lambda-insights-extension.rpm | cpio -imdv && \
    rm -f /tmp/lambda-insights-extension.rpm && \
    if [ "$(uname -m)" = "aarch64" ] ; then patchelf --set-interpreter /lib64/ld-linux-aarch64.so.1 /opt/extensions/cloudwatch_lambda_agent ; fi && \
    removepkg cpio icu4c libgcrypt libgpg-error lua patchelf rpm sqlite


FROM base AS python-base

RUN export TERSE=0 && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on install python3 python-pip expat || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current

FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4@sha256:e2653f741cd15851ba4f13f3cc47d29f2d14377c7d11737bfa272baa1b569007 AS aws-lambda-adapter


FROM python-base AS poetry

# renovate: datasource=git-refs depName=https://github.com/python-poetry/install.python-poetry.org
ARG POETRY_INSTALLER_VERSION=d62875fc05fb20062175cd14d19a96dbefa48640

# renovate: datasource=github-releases depName=python-poetry/poetry
ARG POETRY_VERSION=1.8.3

# renovate: datasource=github-releases depName=python-poetry/poetry-plugin-export
ARG POETRY_PLUGIN_EXPORT_VERSION=1.8.0

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/install.python-poetry.org/$POETRY_INSTALLER_VERSION/install-poetry.py | POETRY_VERSION=$POETRY_VERSION /usr/bin/python3 - && \
    export PATH="/root/.local/bin:$PATH" && \
    poetry config warnings.export false && \
    poetry self add poetry-plugin-export==$POETRY_PLUGIN_EXPORT_VERSION && \
    rm -rf /root/.cache


FROM poetry AS requirements
WORKDIR /tmp/work

COPY pyproject.toml poetry.lock ./

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN export PATH="/root/.local/bin:$PATH" && \
    mkdir -p /tmp/requirements/ && \
    poetry export --no-interaction --format=requirements.txt --output /tmp/requirements/requirements.txt && \
    rm -rf /root/.cache


FROM poetry AS wheels
WORKDIR /src

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN --mount=target=/src,source=. \
    echo "Running with python $(python3 --version)" && \
    [[ "$(cat .python-version)" == "$(python3 --version | cut -d' ' -f2)" ]] || { echo "Python version mismatch" ; exit 1 ; } && \
    export PATH="/root/.local/bin:$PATH" && \
    poetry build --format=wheel --output=/tmp/dist --no-cache && \
    rm -rf /root/.cache


FROM python-base

# COPY --link --from=lambda-layers /opt /opt
COPY --link --from=aws-lambda-adapter /lambda-adapter /opt/extensions/lambda-adapter

COPY lambda-entrypoint.sh /lambda-entrypoint.sh
COPY startup.sh /startup.sh

ENV AWS_LWA_PORT="8000"
ENV AWS_LWA_READINESS_CHECK_PORT="8000"
ENV AWS_LWA_READINESS_CHECK_PATH="/healthz"
ENV AWS_LWA_ASYNC_INIT="true"

# hadolint ignore=DL3013
RUN --mount=type=bind,from=requirements,source=/tmp/requirements,target=/requirements \
    pip3 install --require-hashes --disable-pip-version-check --no-color --no-python-version-warning --no-cache-dir --timeout 100 --no-input -r /requirements/requirements.txt

# hadolint ignore=DL3013
RUN --mount=type=bind,from=wheels,source=/tmp/dist,target=/dist \
    pip3 install --no-color --no-python-version-warning --no-cache-dir --timeout 100 --no-input --no-deps /dist/*.whl

CMD ["/lambda-entrypoint.sh"]
