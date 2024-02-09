# syntax=docker/dockerfile:1.6.0@sha256:ac85f380a63b13dfcefa89046420e1781752bab202122f8f50032edf31be0021

FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.8.1@sha256:330e3bd51eb8ee18a1aa0e77690d1e59fed9c138167af96d63d1710d039c8ae3 AS aws-lambda-adapter

FROM aclemons/slackware:current@sha256:b8775eed7ca7f9110db12ca6e61c16b8d1d610afd3305fbba0578f354f1068fa as base

COPY --from=aws-lambda-adapter --link /lambda-adapter /opt/extensions/lambda-adapter

RUN export TERSE=0 && \
    sed -i '/^WGETFLAGS/s/"$/ -q"/' /etc/slackpkg/slackpkg.conf && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    slackpkg -default_answer=yes -batch=on install brotli ca-certificates cyrus-sasl curl dcron nghttp2 perl && \
    c_rehash && update-ca-certificates && \
    slackpkg -default_answer=yes -batch=on install python3 && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current

ENV EXTENSION_VERSION=1.0.273.0
ENV EXTENSION_CHECKSUM_ARM64=e5fab2b54d46e056a26fc198290305097f1dfd45094a026ad6b84b0f7924d366afe1ea9e9142ea38d66604137c191db30332d25cdc984d6d62720b681d26b208
ENV EXTENSION_CHECKSUM_AMD64=0338b923a89fd3dc86672f2776a04d41961a888fa4d360b7a2309ecb81f24d37c52c92ff350e184f3fbd6dce31605b7d40c77a9e4fb22fd1ba43d72fc2c35992

WORKDIR /
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN export TERSE=0 && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    slackpkg -default_answer=yes -batch=on install cpio icu4c libgcrypt libgpg-error lua patchelf rpm sqlite b&& \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current && \
    if [ "$(uname -m)" = "x86_64" ] ; then curl -o "/tmp/lambda-insights-extension.rpm" -L "https://lambda-insights-extension.s3-ap-northeast-1.amazonaws.com/amazon_linux/lambda-insights-extension.$EXTENSION_VERSION.rpm" ; fi && \
    if [ "$(uname -m)" = "x86_64" ] ; then echo "$EXTENSION_CHECKSUM_AMD64 /tmp/lambda-insights-extension.rpm" | sha512sum --strict --check ; fi && \
    if [ "$(uname -m)" = "aarch64" ] ; then curl -o "/tmp/lambda-insights-extension.rpm" -L "https://lambda-insights-extension-arm64.s3-ap-northeast-1.amazonaws.com/amazon_linux/lambda-insights-extension-arm64.$EXTENSION_VERSION.rpm" ; fi && \
    if [ "$(uname -m)" = "aarch64" ] ; then echo "$EXTENSION_CHECKSUM_ARM64 /tmp/lambda-insights-extension.rpm" | sha512sum --strict --check ; fi && \
    rpm2cpio < "/tmp/lambda-insights-extension.rpm" | cpio -imdv && \
    rm -f /tmp/lambda-insights-extension-arm64*.rpm && \
    if [ "$(uname -m)" = "aarch64" ] ; then patchelf --set-interpreter /lib64/ld-linux-aarch64.so.1 /opt/extensions/cloudwatch_lambda_agent ; fi && \
    removepkg cpio icu4c libgcrypt libgpg-error lua patchelf rpm sqlite

RUN groupadd --gid 1000 python && \
    useradd --uid 1000 --gid python --shell /bin/bash --create-home python && \
    mkdir -p /usr/src/app && chown python:python /usr/src/app

FROM base as builder
WORKDIR /usr/src/app
USER python

COPY --chown=python:python pyproject.toml poetry.lock ./

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# hadolint ignore=SC1091
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.7.1 python3 - && \
    export PATH="/home/python/.local/bin:$PATH" && \
    poetry config warnings.export false && \
    poetry self add poetry-plugin-export==1.6.0 && \
    poetry export --no-interaction --format=requirements.txt --output requirements.txt && \
    curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.7.1 python3 - --uninstall && \
    rm -rf /home/python/.local && rm -rf /home/python/.config && rm -rf /home/python/.cache && \
    rm -rf pyproject.toml poetry.lock && \
    python3 -m venv .venv && \
    source .venv/bin/activate && \
    pip3 install --disable-pip-version-check --no-color --no-python-version-warning --no-cache-dir --timeout 100 --no-input -r requirements.txt && \
    rm requirements.txt

FROM base
WORKDIR /usr/src/app
USER python

COPY lambda-entrypoint.sh /usr/src/app/lambda-entrypoint.sh

ENV AWS_LWA_PORT="8000"
ENV AWS_LWA_READINESS_CHECK_PORT="8000"
ENV AWS_LWA_READINESS_CHECK_PATH="/healthz"

COPY --from=builder /usr/src/app/.venv .venv
COPY --chown=python:python sbobot sbobot

CMD ["/usr/src/app/lambda-entrypoint.sh"]
