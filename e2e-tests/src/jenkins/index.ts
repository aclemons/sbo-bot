import {
  IWireMockRequest,
  IWireMockResponse,
  WireMock,
} from 'wiremock-captain';

export const mockJenkinsSingleMrBuild = async ({
  mrId,
  issueId,
  build,
}: {
  mrId?: number | null;
  issueId?: number | null;
  build: string;
}): Promise<null> => {
  const wiremockEndpoint = 'http://localhost:9100';
  const mock = new WireMock(wiremockEndpoint);

  const jenkinsRequest: IWireMockRequest = {
    method: 'POST',
    endpoint: '/generic-webhook-trigger/invoke',
    body: {
      build_arch: 'x86_64',
      gl_mr: mrId ?? null,
      gl_issue: issueId ?? null,
      build_package: build,
      action: 'build',
      repo: 'SlackBuilds.org/slackbuilds',
    },
  };
  const jenkinsResponse: IWireMockResponse = {
    status: 200,
    body: {
      jobs: {
        'slackbuilds.org-pr-check-build-package': {
          regexpFilterExpression:
            '^(build|rebuild|lint),(x86_64|amd64|i586|arm),-?[1-9][0-9]*,-?[1-9][0-9]*,-*[1-9][0-9]*,-*[1-9][0-9]*,(all|[a-zA-Z]+/[a-zA-Z0-9\\+\\-\\._]+),(SlackBuildsOrg|SlackBuilds\\.org)/.+$',
          triggered: true,
          resolvedVariables: {
            action: 'build',
            build_arch: 'x86_64',
            build_package: build,
            gh_issue: '-1',
            gh_pr: '-1',
            gl_mr: mrId?.toString(),
            repo: 'SlackBuilds.org/slackbuilds',
          },
          regexpFilterText: `build,x86_64,${mrId?.toString() ?? '-1'},${issueId?.toString() ?? '-1'},-1,-1,${build},SlackBuilds.org/slackbuilds`,
          id: 4053,
          url: 'queue/item/4053/',
        },
      },
      message: 'Triggered jobs.',
    },
  };
  await mock.register(jenkinsRequest, jenkinsResponse);

  return null;
};

export const mockJenkinsSinglePrBuild = async ({
  prId,
  issueId,
  build,
}: {
  prId?: number | null;
  issueId?: number | null;
  build: string;
}): Promise<null> => {
  const wiremockEndpoint = 'http://localhost:9100';
  const mock = new WireMock(wiremockEndpoint);

  const jenkinsRequest: IWireMockRequest = {
    method: 'POST',
    endpoint: '/generic-webhook-trigger/invoke',
    body: {
      build_arch: 'x86_64',
      gh_pr: prId ?? null,
      gh_issue: issueId ?? null,
      build_package: build,
      repo: 'SlackBuildsOrg/slackbuilds',
      action: 'build',
    },
  };
  const jenkinsResponse: IWireMockResponse = {
    status: 200,
    body: {
      jobs: {
        'slackbuilds.org-pr-check-build-package': {
          regexpFilterExpression:
            '^(build|rebuild|lint),(x86_64|amd64|i586|arm),-?[1-9][0-9]*,-?[1-9][0-9]*,-*[1-9][0-9]*,-*[1-9][0-9]*,(all|[a-zA-Z]+/[a-zA-Z0-9\\+\\-\\._]+),(SlackBuildsOrg|SlackBuilds\\.org)/.+$',
          triggered: true,
          resolvedVariables: {
            action: 'build',
            build_arch: 'x86_64',
            build_package: build,
            gh_issue: issueId?.toString() ?? '-1',
            gh_pr: prId?.toString() ?? '-1',
            gl_mr: '-1',
            repo: 'SlackBuildsOrg/slackbuilds',
          },
          regexpFilterText: `build,x86_64,-1,-1,${prId?.toString() ?? '-1'},${issueId?.toString() ?? '-1'},${build},SlackBuilds.org/slackbuilds`,
          id: 4053,
          url: 'queue/item/4053/',
        },
      },
      message: 'Triggered jobs.',
    },
  };
  await mock.register(jenkinsRequest, jenkinsResponse);

  return null;
};
