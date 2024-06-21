# syntax=docker/dockerfile:1.8.1@sha256:e87caa74dcb7d46cd820352bfea12591f3dba3ddc4285e19c7dcd13359f7cefd

FROM aclemons/slackware:current@sha256:ec9d721235a86d677ac5654ff832681477d7fbb6af349814f50b7df4da156b79 AS base

RUN export TERSE=0 && \
    sed -i '/^WGETFLAGS/s/"$/ -q"/' /etc/slackpkg/slackpkg.conf && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on install brotli ca-certificates cyrus-sasl curl dcron nghttp2 perl || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    c_rehash && update-ca-certificates && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current

# renovate: datasource=github-releases depName=aws/aws-lambda-runtime-interface-emulator
ARG AWS_LAMBDA_RIE_VERSION=v1.20

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
    EXIT_CODE=0 && slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on install cpio icu4c libgcrypt libgpg-error lua patchelf rpm sqlite || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current && \
    if [ "$(uname -m)" = "x86_64" ] ; then curl -o "/tmp/lambda-insights-extension.rpm" -L "https://lambda-insights-extension.s3-ap-northeast-1.amazonaws.com/amazon_linux/lambda-insights-extension.$EXTENSION_VERSION.rpm" ; fi && \
    if [ "$(uname -m)" = "x86_64" ] ; then echo "$EXTENSION_CHECKSUM_AMD64 /tmp/lambda-insights-extension.rpm" | sha512sum --strict --check ; fi && \
    if [ "$(uname -m)" = "aarch64" ] ; then curl -o "/tmp/lambda-insights-extension.rpm" -L "https://lambda-insights-extension-arm64.s3-ap-northeast-1.amazonaws.com/amazon_linux/lambda-insights-extension-arm64.$EXTENSION_VERSION.rpm" ; fi && \
    if [ "$(uname -m)" = "aarch64" ] ; then echo "$EXTENSION_CHECKSUM_ARM64 /tmp/lambda-insights-extension.rpm" | sha512sum --strict --check ; fi && \
    rpm2cpio < "/tmp/lambda-insights-extension.rpm" | cpio -imdv && \
    rm -f /tmp/lambda-insights-extension.rpm && \
    if [ "$(uname -m)" = "aarch64" ] ; then patchelf --set-interpreter /lib64/ld-linux-aarch64.so.1 /opt/extensions/cloudwatch_lambda_agent ; fi && \
    removepkg cpio icu4c libgcrypt libgpg-error lua patchelf rpm sqlite


FROM base AS python-base

RUN export TERSE=0 && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on install python3 expat || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current

RUN groupadd --gid 1000 python && \
    useradd --uid 1000 --gid python --shell /bin/bash --create-home python && \
    mkdir -p /usr/src/app && chown python:python /usr/src/app

FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3@sha256:f312209a538c102bcc112b99edf9b989140658a5f8d0c98d9a0c7ce12512e76a AS aws-lambda-adapter


FROM python-base AS builder
WORKDIR /usr/src/app
USER python

COPY --chown=python:python .python-version pyproject.toml poetry.lock ./

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# hadolint ignore=SC1091
RUN echo "Running with python $(python3 --version)" && \
    [[ "$(cat .python-version)" == "$(python3 --version | cut -d' ' -f2)" ]] || { echo "Python version mismatch" ; exit 1 ; } && \
    curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.8.3 python3 - && \
    export PATH="/home/python/.local/bin:$PATH" && \
    poetry config warnings.export false && \
    poetry self add poetry-plugin-export==1.8.0 && \
    poetry export --no-interaction --format=requirements.txt --output requirements.txt && \
    curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.8.3 python3 - --uninstall && \
    rm -rf /home/python/.local && rm -rf /home/python/.config && rm -rf /home/python/.cache && \
    rm -rf .python-version pyproject.toml poetry.lock && \
    python3 -m venv .venv && \
    source .venv/bin/activate && \
    pip3 install --disable-pip-version-check --no-color --no-python-version-warning --no-cache-dir --timeout 100 --no-input -r requirements.txt && \
    rm requirements.txt

FROM python-base

# COPY --link --from=lambda-layers /opt /opt
COPY --link --from=aws-lambda-adapter /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /usr/src/app
USER python

COPY lambda-entrypoint.sh /lambda-entrypoint.sh
COPY startup.sh /startup.sh

ENV AWS_LWA_PORT="8000"
ENV AWS_LWA_READINESS_CHECK_PORT="8000"
ENV AWS_LWA_READINESS_CHECK_PATH="/healthz"
ENV AWS_LWA_ASYNC_INIT="true"

COPY --link --from=builder /usr/src/app/.venv .venv
COPY --chown=python:python sbobot sbobot

CMD ["/lambda-entrypoint.sh"]
