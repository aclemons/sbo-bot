import {
  IWireMockRequest,
  IWireMockResponse,
  WireMock,
} from 'wiremock-captain';

export const buildCommentWebhookPayload = async ({
  username,
  build,
}: {
  username: String;
  build: String;
}): Promise<{
  prId: Number;
  commentId: Number;
  payload: String;
  signature: String;
}> => {
  const min = 0;
  const max = 65535;

  const prId = Math.floor(Math.random() * (max - min + 1)) + min;
  const commentId = Math.floor(Math.random() * (max - min + 1)) + min;

  const payloadObject = {
    action: 'created',
    issue: {
      number: prId,
      title: build,
      user: {
        login: username,
      },
      pull_request: {},
    },
    comment: {
      id: commentId,
      user: {
        login: username,
      },
      body: `@sbo-bot: build x86_64 ${build}`,
    },
    repository: {
      id: 49907051,
      name: 'slackbuilds',
      full_name: 'SlackBuildsOrg/slackbuilds',
      owner: {
        login: 'SlackBuildsOrg',
      },
    },
    organization: {
      login: 'SlackBuildsOrg',
    },
    sender: {
      login: username,
    },
    installation: {
      id: 123,
    },
  };

  const payload = JSON.stringify(payloadObject);

  const encoder = new TextEncoder();
  const algorithm = { name: 'HMAC', hash: { name: 'SHA-256' } };
  const keyBytes = encoder.encode('AL1lYqj3G6Va3DnhUNkXKU93EtdShteb');
  const key = await crypto.subtle.importKey('raw', keyBytes, algorithm, false, [
    'sign',
    'verify',
  ]);

  const dataBytes = encoder.encode(payload);
  const signatureBytes = await crypto.subtle.sign(
    algorithm.name,
    key,
    dataBytes,
  );
  const signature = Buffer.from(signatureBytes).toString('hex');

  return {
    payload,
    prId,
    commentId,
    signature,
  };
};

export const mockCommentAck = async ({
  prId,
  commentId,
}: {
  prId: Number;
  commentId: Number;
}): Promise<null> => {
  const wiremockEndpoint = 'http://localhost:9100';
  const mock = new WireMock(wiremockEndpoint);

  const getAccessTokenRequest: IWireMockRequest = {
    method: 'POST',
    endpoint: '/api/v3/app/installations/123/access_tokens',
  };
  const getAccessTokenResponse: IWireMockResponse = {
    status: 200,
    body: {
      token: 'ghs_1234567',
    },
  };
  await mock.register(getAccessTokenRequest, getAccessTokenResponse);

  const reactionRequest: IWireMockRequest = {
    method: 'POST',
    endpoint: `/api/v3/repos/SlackBuildsOrg/slackbuilds/issues/comments/${commentId}/reactions`,
    body: {
      content: '+1',
    },
  };
  const reactionResponse: IWireMockResponse = {
    status: 200,
    body: {
      content: '+1',
    },
  };
  await mock.register(reactionRequest, reactionResponse);

  return null;
};
