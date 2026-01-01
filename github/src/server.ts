import Express from 'express';

import { createNodeMiddleware, createProbot } from 'probot';

import app from './index.ts';

const probot = createProbot({ env: process.env });
const express = Express();

const middleware = await createNodeMiddleware(app, {
  probot,
  webhooksPath: '/',
});

express.use(middleware);
express.use(Express.json());

express.get('/healthz', (_, resp) => {
  resp.setHeader('content-type', 'text/plain');
  resp.end('ok');
});

express.listen(3000, () => {
  console.log(`Server is running at http://localhost:3000`);
});
