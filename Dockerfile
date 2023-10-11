FROM aclemons/slackware:current@sha256:38b110a8b49b980791a548465debf7dc4dec434fc4471c833b9b8a3c14af7a32 as base

RUN export TERSE=0 && \
    sed -i '/^WGETFLAGS/s/"$/ -q"/' /etc/slackpkg/slackpkg.conf && \
    slackpkg -default_answer=yes -batch=on update && \
    EXIT_CODE=0 && slackpkg -default_answer=yes -batch=on upgrade-all || EXIT_CODE=$? && \
    if [ "$EXIT_CODE" -ne 0 ] && [ "$EXIT_CODE" -ne 20 ] ; then exit "$EXIT_CODE" ; fi && \
    slackpkg -default_answer=yes -batch=on install brotli ca-certificates cyrus-sasl curl dcron nghttp2 perl && \
    slackpkg -default_answer=yes -batch=on install nodejs libuv icu4c && \
    rm -rf /var/cache/packages/* && rm -rf /var/lib/slackpkg/* && \
    touch /var/lib/slackpkg/current && \
    c_rehash && update-ca-certificates && \
    npm config set update-notifier false

RUN groupadd --gid 1000 node && \
  useradd --uid 1000 --gid node --shell /bin/bash --create-home node && \
  mkdir -p /usr/src/app && chown node:node /usr/src/app


FROM base as builder
WORKDIR /usr/src/app
USER node

COPY --chown=node:node package.json package-lock.json ./
RUN npm ci && npm cache clean --force

COPY --chown=node:node . ./

RUN npm run build


FROM base
ENV NODE_ENV production
ENV LOG_LEVEL debug
WORKDIR /usr/src/app
USER node

COPY --chown=node:node package.json package-lock.json ./

RUN npm ci --omit=dev && npm cache clean --force

COPY --from=builder /usr/src/app/lib lib

CMD ["node_modules/.bin/probot", "run", "/usr/src/app/lib/index.js"]
