FROM node:20.6.0-slim@sha256:e1eb4a77df4da741c10c17497cec32898692d849d4b4c5a7d214b13604b9fa7d
WORKDIR /usr/src/app
COPY package.json package-lock.json ./
RUN npm ci --production && npm cache clean --force
ENV NODE_ENV="production"
COPY . .
CMD ["npm", "start"]
