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
