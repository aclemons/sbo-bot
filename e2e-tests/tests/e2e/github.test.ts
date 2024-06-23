import { buildCommentWebhookPayload, mockCommentAck } from '../../src/github';
import { mockJenkinsSinglePrBuild } from '../../src/jenkins';
import { beforeEach, describe, expect, it } from '@jest/globals';
import supertest from 'supertest';
import { WireMock } from 'wiremock-captain';

describe('github webhook', () => {
  beforeEach(async () => {
    const wiremockEndpoint = 'http://localhost:9100';
    const mock = new WireMock(wiremockEndpoint);
    await mock.resetMappings();
  });

  describe('pOST /', () => {
    describe('a single build is requested by an admin', () => {
      it('schedules the build', async () => {
        expect.assertions(1);

        const build = 'system/fzf';
        const { payload, prId, commentId, signature } =
          await buildCommentWebhookPayload({
            username: 'testadmin1',
            build,
          });

        await mockJenkinsSinglePrBuild({ prId, build });
        await mockCommentAck({ commentId });

        const res = await supertest('http://localhost:9011')
          .post('/')
          .set('content-type', 'application/json')
          .set('x-github-delivery', crypto.randomUUID())
          .set('x-github-event', 'issue_comment')
          .set('x-hub-signature-256', `sha256=${signature}`)
          .send(payload);

        expect(res.statusCode).toBe(200);
      });
    });

    describe('a single build is requested by normal user', () => {
      it('ignores the comment', async () => {
        expect.assertions(1);

        const build = 'system/fzf';
        const { payload, signature } = await buildCommentWebhookPayload({
          username: 'randomuser',
          build,
        });

        const res = await supertest('http://localhost:9011')
          .post('/')
          .set('content-type', 'application/json')
          .set('x-github-delivery', crypto.randomUUID())
          .set('x-github-event', 'issue_comment')
          .set('x-hub-signature-256', `sha256=${signature}`)
          .send(payload);

        expect(res.statusCode).toBe(200);
      });
    });
  });
});
