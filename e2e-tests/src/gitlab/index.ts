import {
  IWireMockRequest,
  IWireMockResponse,
  WireMock,
} from 'wiremock-captain';

export const buildCommentWebhookPayload = ({
  username,
  build,
}: {
  username: string;
  build: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
}): { mrId: number; commentId: number; payload: any } => {
  const min = 0;
  const max = 65535;

  const mrId = Math.floor(Math.random() * (max - min + 1)) + min;
  const commentId = Math.floor(Math.random() * (max - min + 1)) + min;

  const payload = {
    object_kind: 'note',
    event_type: 'note',
    user: {
      username: username,
    },
    project_id: 1309714,
    project: {
      id: 1309714,
      path_with_namespace: 'SlackBuilds.org/slackbuilds',
    },
    object_attributes: {
      id: commentId,
      note: `@sbo-bot: build x86_64 ${build}`,
      noteable_type: 'MergeRequest',
    },
    merge_request: {
      iid: mrId,
    },
  };

  return {
    payload,
    mrId,
    commentId,
  };
};

export const mockCommentAck = async ({
  mrId,
  commentId,
}: {
  mrId: number;
  commentId: number;
}): Promise<null> => {
  const wiremockEndpoint = 'http://localhost:9100';
  const mock = new WireMock(wiremockEndpoint);

  const gitlabRequest: IWireMockRequest = {
    method: 'POST',
    endpoint: `/api/v4/projects/1309714/merge_requests/${mrId.toString()}/notes/${commentId.toString()}/award_emoji`,
    body: {
      name: 'thumbsup',
    },
  };
  const gitlabResponse: IWireMockResponse = {
    status: 200,
    body: {},
  };
  await mock.register(gitlabRequest, gitlabResponse);

  return null;
};
