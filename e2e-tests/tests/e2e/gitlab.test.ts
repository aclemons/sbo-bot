import { buildCommentWebhookPayload, mockCommentAck } from '../../src/gitlab';
import { mockJenkinsSingleMrBuild } from '../../src/jenkins';
import { beforeEach, describe, expect, it } from '@jest/globals';
import supertest from 'supertest';
import { WireMock } from 'wiremock-captain';

describe('gitlab webhook', () => {
  beforeEach(async () => {
    const wiremockEndpoint = 'http://localhost:9100';
    const mock = new WireMock(wiremockEndpoint);
    await mock.resetMappings();
  });

  describe('an HTTP POST to /webhook', () => {
    describe('a single build is requested by an admin on an MR', () => {
      it('schedules the build', async () => {
        expect.assertions(1);

        const build = 'system/fzf';
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        const { payload, mrId, commentId } = buildCommentWebhookPayload({
          username: 'testadmin1',
          build,
        });

        await mockJenkinsSingleMrBuild({ mrId, build });
        await mockCommentAck({ mrId, commentId });

        const res = await supertest('http://localhost:9012')
          .post('/webhook')
          .set('x-gitlab-token', '123456')
          // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
          .send(payload);

        expect(res.statusCode).toBe(204);
      });
    });

    describe('a single build is requested by an admin on an issue', () => {
      it('schedules the build', async () => {
        expect.assertions(1);

        const build = 'system/fzf';
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        const { payload, issueId, commentId } = buildCommentWebhookPayload({
          username: 'testadmin1',
          build,
          issue: true,
        });

        await mockJenkinsSingleMrBuild({ issueId, build });
        await mockCommentAck({ issueId, commentId });

        const res = await supertest('http://localhost:9012')
          .post('/webhook')
          .set('x-gitlab-token', '123456')
          // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
          .send(payload);

        expect(res.statusCode).toBe(204);
      });
    });

    describe('a single build is requested by normal user', () => {
      it('ignores the comment', async () => {
        expect.assertions(1);

        const build = 'system/fzf';
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        const { payload } = buildCommentWebhookPayload({
          username: 'randomuser',
          build,
        });

        const res = await supertest('http://localhost:9012')
          .post('/webhook')
          .set('x-gitlab-token', '123456')
          // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
          .send(payload);

        expect(res.statusCode).toBe(204);
      });
    });
  });
});
