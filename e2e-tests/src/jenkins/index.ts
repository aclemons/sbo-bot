import {
  IWireMockRequest,
  IWireMockResponse,
  WireMock,
} from 'wiremock-captain';

export const mockJenkinsSingleMrBuild = async ({
  mrId,
  build,
}: {
  mrId: Number;
  build: String;
}): Promise<null> => {
  const wiremockEndpoint = 'http://localhost:9100';
  const mock = new WireMock(wiremockEndpoint);

  const jenkinsRequest: IWireMockRequest = {
    method: 'POST',
    endpoint: '/generic-webhook-trigger/invoke',
    body: {
      build_arch: 'x86_64',
      gl_mr: mrId,
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
            '^(build|rebuild|lint),(x86_64|amd64|i586|arm),-?[1-9][0-9]*,-*[1-9][0-9]*,-*[1-9][0-9]*,(all|[a-zA-Z]+/[a-zA-Z0-9\\+\\-\\._]+),(SlackBuildsOrg|SlackBuilds\\.org)/.+$',
          triggered: true,
          resolvedVariables: {
            action: 'build',
            build_arch: 'x86_64',
            build_package: build,
            gh_issue: '-1',
            gh_pr: '-1',
            gl_mr: `${mrId}`,
            repo: 'SlackBuilds.org/slackbuilds',
          },
          regexpFilterText: `build,x86_64,${mrId},-1,-1,${build},SlackBuilds.org/slackbuilds`,
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
