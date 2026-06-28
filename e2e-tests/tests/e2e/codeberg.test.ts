import {
  buildCommentWebhookPayload,
  mockCommentAck,
  mockCommentAckFailure,
} from '../../src/codeberg';
import { mockJenkinsSingleCodebergBuild } from '../../src/jenkins';
import supertest from 'supertest';
import { beforeEach, describe, expect, it } from 'vitest';
import { WireMock } from 'wiremock-captain';

describe('codeberg webhook', () => {
  beforeEach(async () => {
    const wiremockEndpoint = 'http://localhost:9100';
    const mock = new WireMock(wiremockEndpoint);
    await mock.resetMappings();
  });

  describe('an HTTP POST to /codeberg/webhook', () => {
    describe('a single build is requested by an admin on a PR', () => {
      it('schedules the build', async () => {
        expect.assertions(1);

        const build = 'system/fzf';
        const { payload, mrId, commentId } = buildCommentWebhookPayload({
          username: 'testadmin1',
          build,
        });

        await mockJenkinsSingleCodebergBuild({ prId: mrId, build });
        await mockCommentAck({ commentId });

        const res = await supertest('http://localhost:9012')
          .post('/codeberg/webhook')
          .set('authorization', 'Bearer 123456')
          .send(payload);

        expect(res.statusCode).toBe(204);
      });

      it('still returns success when adding the ack reaction fails', async () => {
        expect.assertions(1);

        const build = 'system/fzf';
        const { payload, mrId, commentId } = buildCommentWebhookPayload({
          username: 'testadmin1',
          build,
        });

        await mockJenkinsSingleCodebergBuild({ prId: mrId, build });
        await mockCommentAckFailure({ commentId });

        const res = await supertest('http://localhost:9012')
          .post('/codeberg/webhook')
          .set('authorization', 'Bearer 123456')
          .send(payload);

        expect(res.statusCode).toBe(204);
      });
    });
  });
});
