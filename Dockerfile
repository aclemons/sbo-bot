FROM node:20.5.1-slim@sha256:75404fc5825f24222276501c09944a5bee8ed04517dede5a9934f1654ca84caf
WORKDIR /usr/src/app
COPY package.json package-lock.json ./
RUN npm ci --production && npm cache clean --force
ENV NODE_ENV="production"
COPY . .
CMD ["npm", "start"]
