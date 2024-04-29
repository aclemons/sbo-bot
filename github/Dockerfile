# syntax=docker/dockerfile:1.7.1@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3@sha256:f312209a538c102bcc112b99edf9b989140658a5f8d0c98d9a0c7ce12512e76a AS aws-lambda-adapter

FROM aclemons/slackware:current@sha256:d2486923f0e934f2f8c9b221d841e18013618070ca820a2ca547ee5bdeca4976 as base

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
