import { buildCommentWebhookPayload, mockCommentAck } from '../../src/gitlab';
import { mockJenkinsSingleMrBuild } from '../../src/jenkins';
import supertest from 'supertest';
import { WireMock } from 'wiremock-captain';

describe('gitlab webhook', () => {
  beforeEach(async () => {
    const wiremockEndpoint = 'http://localhost:9100';
    const mock = new WireMock(wiremockEndpoint);
    await mock.resetMappings();
  });

  describe('POST /webhook', () => {
    describe('a single build is requested by an admin', () => {
      it('schedules the build', async () => {
        const build = 'system/fzf';
        const { payload, mrId, commentId } = buildCommentWebhookPayload({
          username: 'testadmin1',
          build,
        });

        await mockJenkinsSingleMrBuild({ mrId, build });
        await mockCommentAck({ mrId, commentId });

        const res = await supertest('http://localhost:9012')
          .post('/webhook')
          .set('x-gitlab-token', '123456')
          .send(payload);

        expect(res.statusCode).toBe(204);
      });
    });

    describe('a single build is requested by normal user', () => {
      it('ignores the comment', async () => {
        const build = 'system/fzf';
        const { payload, mrId, commentId } = buildCommentWebhookPayload({
          username: 'randomuser',
          build,
        });

        const res = await supertest('http://localhost:9012')
          .post('/webhook')
          .set('x-gitlab-token', '123456')
          .send(payload);

        expect(res.statusCode).toBe(204);
      });
    });
  });
});
