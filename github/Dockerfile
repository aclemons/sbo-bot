# syntax=docker/dockerfile:1.7.0@sha256:dbbd5e059e8a07ff7ea6233b213b36aa516b4c53c645f1817a4dd18b83cbea56

FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.8.1@sha256:330e3bd51eb8ee18a1aa0e77690d1e59fed9c138167af96d63d1710d039c8ae3 AS aws-lambda-adapter

FROM aclemons/slackware:current@sha256:2ecc3620d15aa0d9f2845a43bbe53ead7876ad65633ff3b04c9710c0226f80a0 as base

COPY --from=aws-lambda-adapter --link /lambda-adapter /opt/extensions/lambda-adapter

RUN export TERSE=0 && \
    sed -i '/^WGETFLAGS/s/"$/ -q"/' /etc/slackpkg/slackpkg.conf && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    slackpkg -default_answer=yes -batch=on install brotli ca-certificates cyrus-sasl curl dcron nghttp2 perl && \
    c_rehash && update-ca-certificates && \
    slackpkg -default_answer=yes -batch=on install nodejs libuv icu4c && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current

RUN groupadd --gid 1000 node && \
    useradd --uid 1000 --gid node --shell /bin/bash --create-home node && \
    mkdir -p /usr/src/app && chown node:node /usr/src/app


FROM base as builder
WORKDIR /usr/src/app
USER node

RUN npm config set update-notifier false

COPY --chown=node:node package.json package-lock.json ./
RUN npm ci && npm cache clean --force

COPY --chown=node:node . ./

RUN npm run build


FROM base
WORKDIR /usr/src/app
USER node

COPY lambda-entrypoint.sh /usr/src/app/lambda-entrypoint.sh

ENV NODE_ENV production
ENV LOG_LEVEL debug
ENV AWS_LWA_PORT="3000"
ENV AWS_LWA_READINESS_CHECK_PORT="3000"
ENV AWS_LWA_READINESS_CHECK_PATH="/healthz"

RUN npm config set update-notifier false

COPY --chown=node:node package.json package-lock.json ./

RUN npm ci --omit=dev && npm cache clean --force

COPY --from=builder /usr/src/app/lib lib

CMD ["/usr/src/app/lambda-entrypoint.sh"]
