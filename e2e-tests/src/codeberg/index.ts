import {
  IWireMockRequest,
  IWireMockResponse,
  WireMock,
} from 'wiremock-captain';

export const buildCommentWebhookPayload = ({
  username,
  build,
  issue,
}: {
  username: string;
  build: string;
  issue?: boolean;
}): {
  mrId: number | null;
  issueId: number | null;
  commentId: number;
  payload: Record<string, unknown>;
} => {
  const min = 0;
  const max = 65535;

  const userId = Math.floor(Math.random() * (max - min + 1)) + min;
  const commentId = Math.floor(Math.random() * (max - min + 1)) + min;
  const repository = {
    id: 1309714,
    full_name: 'SlackBuilds.org/slackbuilds',
  };

  let payload: Record<string, unknown>;
  let issueId: number | null = null;
  let mrId: number | null = null;

  if (issue) {
    issueId = Math.floor(Math.random() * (max - min + 1)) + min;

    payload = {
      comment: {
        id: commentId,
        body: `@sbo-bot: build x86_64 ${build}`,
      },
      sender: {
        id: userId,
        login: username,
      },
      repository,
      issue: {
        number: issueId,
        user: {
          id: userId,
        },
      },
    };
  } else {
    mrId = Math.floor(Math.random() * (max - min + 1)) + min;

    payload = {
      comment: {
        id: commentId,
        body: `@sbo-bot: build x86_64 ${build}`,
      },
      sender: {
        id: userId,
        login: username,
      },
      repository,
      pull_request: {
        number: mrId,
        user: {
          id: userId,
        },
      },
    };
  }

  return {
    payload,
    issueId,
    mrId,
    commentId,
  };
};

export const mockCommentAck = async ({
  commentId,
}: {
  commentId: number;
}): Promise<null> => {
  return mockCommentAckWithStatus({
    commentId,
    status: 200,
  });
};

export const mockCommentAckFailure = async ({
  commentId,
}: {
  commentId: number;
}): Promise<null> => {
  return mockCommentAckWithStatus({
    commentId,
    status: 500,
  });
};

const mockCommentAckWithStatus = async ({
  commentId,
  status,
}: {
  commentId: number;
  status: number;
}): Promise<null> => {
  const wiremockEndpoint = 'http://localhost:9100';
  const mock = new WireMock(wiremockEndpoint);

  const request: IWireMockRequest = {
    method: 'POST',
    endpoint: `/codeberg.org/api/v1/repos/SlackBuilds.org/slackbuilds/issues/comments/${commentId.toString()}/reactions`,
    body: {
      content: '+1',
    },
  };

  const response: IWireMockResponse = {
    status,
    body: {},
  };

  await mock.register(request, response);

  return null;
};
