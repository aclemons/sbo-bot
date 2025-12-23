# syntax=docker/dockerfile:1.20.0@sha256:26147acbda4f14c5add9946e2fd2ed543fc402884fd75146bd342a7f6271dc1d

FROM aclemons/slackware:current@sha256:6a9e4d699e1ff94cf99fca9e80694e0fe831637130d0d8f8a3b3c3bc710fe6f9 AS base

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
ARG AWS_LAMBDA_RIE_VERSION=v1.30

RUN if [ "$(uname -m)" = "aarch64" ] ; then curl -o /usr/local/bin/aws-lambda-rie -L "https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/download/$AWS_LAMBDA_RIE_VERSION/aws-lambda-rie-arm64" ; else curl -o /usr/local/bin/aws-lambda-rie -L "https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/download/$AWS_LAMBDA_RIE_VERSION/aws-lambda-rie-x86_64" ; fi && \
    chown root:root /usr/local/bin/aws-lambda-rie && chmod 0755 /usr/local/bin/aws-lambda-rie


FROM base AS lambda-layers

ENV EXTENSION_VERSION=1.0.660.0
ENV EXTENSION_CHECKSUM_AMD64=256a3aa47b150cba4d8d2338a4abe9ec5d4174386953a08f79bc523c4178ad3e259f394c139a6b725ab39df76c25886c93f3703ceb809a1ddaddd78aacca0006
ENV EXTENSION_CHECKSUM_ARM64=8f3723cd17b95968af167ba5af8fb89ce63ed5b1b8bf84a584c3f0d27f651a26f641103758d76e873ac6433e64b2b4af6a6b09b3643da28e352f40bfd924976c

WORKDIR /
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN export TERSE=0 && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on install cpio icu4c libarchive libgcrypt libgpg-error libxml2 lua lz4 patchelf rpm sqlite || EXIT_CODE=$? ; } && \
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
    removepkg cpio icu4c libgcrypt libarchive libgpg-error libxml2 lua lz4 patchelf rpm sqlite


FROM base AS node-base

RUN export TERSE=0 && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    EXIT_CODE=0 && { slackpkg -default_answer=yes -batch=on install icu4c libuv nodejs || EXIT_CODE=$? ; } && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current

RUN groupadd --gid 1000 node && \
    useradd --uid 1000 --gid node --shell /bin/bash --create-home node && \
    mkdir -p /usr/src/app && chown node:node /usr/src/app


FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1@sha256:46d6625e68cbbdd2efab4a20245977664513f13ffef47915b000d431adcea0b4 AS aws-lambda-adapter


FROM node-base AS builder
WORKDIR /usr/src/app
USER node

RUN npm config set update-notifier false

COPY --chown=node:node package.json package-lock.json ./

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN echo "Running with node $(node --version)" && \
    [[ "$(sed -n '/"engines"/,+1p' package.json | sed -n '$p' | cut -d: -f2 | sed 's/"//g;s/[[:space:]]*//g')" == "$(node --version | sed 's/v//')" ]] || { echo "Node version mismatch" ; exit 1 ; } && \
    npm ci && npm cache clean --force

COPY --chown=node:node . ./

RUN npm run build


FROM node-base

# COPY --link --from=lambda-layers /opt /opt
COPY --link --from=aws-lambda-adapter /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /usr/src/app
USER node

COPY lambda-entrypoint.sh /lambda-entrypoint.sh
COPY startup.sh /startup.sh

ENV NODE_ENV=production
ENV LOG_LEVEL=debug
ENV AWS_LWA_PORT="3000"
ENV AWS_LWA_READINESS_CHECK_PORT="3000"
ENV AWS_LWA_READINESS_CHECK_PATH="/healthz"
ENV AWS_LWA_ASYNC_INIT="true"

RUN npm config set update-notifier false

COPY --chown=node:node package.json package-lock.json ./

RUN npm ci --omit=dev && npm cache clean --force

COPY --from=builder /usr/src/app/lib lib

CMD ["/lambda-entrypoint.sh"]
