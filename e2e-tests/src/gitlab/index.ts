import assert from 'assert';
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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload: any;
} => {
  const min = 0;
  const max = 65535;

  const userId = Math.floor(Math.random() * (max - min + 1)) + min;
  const commentId = Math.floor(Math.random() * (max - min + 1)) + min;
  let payload;
  let issueId = null;
  let mrId = null;
  if (issue) {
    issueId = Math.floor(Math.random() * (max - min + 1)) + min;

    payload = {
      object_kind: 'note',
      event_type: 'note',
      user: {
        username: username,
        id: userId,
      },
      project_id: 1309714,
      project: {
        id: 1309714,
        path_with_namespace: 'SlackBuilds.org/slackbuilds',
      },
      object_attributes: {
        id: commentId,
        note: `@sbo-bot: build x86_64 ${build}`,
        noteable_type: 'Issue',
      },
      issue: {
        iid: issueId,
        author_id: userId,
      },
    };
  } else {
    mrId = Math.floor(Math.random() * (max - min + 1)) + min;

    payload = {
      object_kind: 'note',
      event_type: 'note',
      user: {
        username: username,
        id: userId,
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
        author_id: userId,
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
  mrId,
  issueId,
  commentId,
}: {
  issueId?: number | null;
  mrId?: number | null;
  commentId: number;
}): Promise<null> => {
  const wiremockEndpoint = 'http://localhost:9100';
  const mock = new WireMock(wiremockEndpoint);
  let gitlabRequest: IWireMockRequest;
  if (issueId) {
    gitlabRequest = {
      method: 'POST',
      endpoint: `/api/v4/projects/1309714/issues/${issueId.toString()}/notes/${commentId.toString()}/award_emoji`,
      body: {
        name: 'thumbsup',
      },
    };
  } else {
    assert(mrId);
    gitlabRequest = {
      method: 'POST',
      endpoint: `/api/v4/projects/1309714/merge_requests/${mrId.toString()}/notes/${commentId.toString()}/award_emoji`,
      body: {
        name: 'thumbsup',
      },
    };
  }
  const gitlabResponse: IWireMockResponse = {
    status: 200,
    body: {},
  };
  await mock.register(gitlabRequest, gitlabResponse);

  return null;
};
