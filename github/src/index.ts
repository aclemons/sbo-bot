import { Probot } from 'probot';
import axios from 'axios';

const shutdown = () => {
  console.log('Shutting down server...');
};
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

export = (app: Probot) => {
  const allowedCommentors = (process.env.GITHUB_ADMINS ?? '').split(',');
  const allowedContributors = (process.env.GITHUB_CONTRIBUTORS ?? '').split(',');

  app.on('issue_comment.created', async (context) => {
    context.log.info('Processing comment');

    const { payload } = context;

    if (!process.env.JENKINS_WEBHOOK || !process.env.JENKINS_WEBHOOK_SECRET) {
      context.log.info('Jenkins webhook vars not configured');
      return;
    }

    const comment = payload.comment.body.trim();
    const commentator = payload.comment.user.login;
    const owner = payload.issue.user.login;

    let matches = null;
    if ('pull_request' in payload.issue) {
      if (!allowedCommentors.includes(commentator)) {
        context.log.info(`Comment was not made by an admin. (${commentator})`);

        if (!allowedContributors.includes(commentator)) {
          context.log.info(`Comment was not made by a contributor. (${commentator})`);
          return;
        }

        if (!allowedContributors.includes(owner)) {
          context.log.info(`Comment was not on the contributors own PR. (${owner})`);
          return;
        }
      }

      matches =
        /^@sbo-bot: (single-build|rebuild|build|lint) ((amd64|x86_64|arm|i586) )?([a-zA-z]+\/[a-zA-Z0-9+\-._]+)$/.exec(
          comment,
        );
    } else {
      if (!allowedCommentors.includes(commentator)) {
        context.log.info(`Comment was not made by an admin. (${commentator})`);
        return;
      }

      matches =
        /^@sbo-bot: (single-build|rebuild|build|lint) ((amd64|x86_64|arm|i586) )?([a-zA-z]+\/[a-zA-Z0-9+\-._]+|all)$/.exec(
          comment,
        );
    }

    if (!matches) {
      context.log.info('Comment not a build request.');
      return;
    }

    const action = matches[1] == 'lint' ? 'lint' : matches[1] == 'rebuild' ? 'rebuild' : 'build';
    const build_arch = matches[3];
    const build_package = matches[4];

    if (build_arch) {
      context.log.info(
        `Triggering ${action} of package ${build_package} with requested arch: ${build_arch}.`,
      );
      const { data, status } = await axios.post(
        process.env.JENKINS_WEBHOOK,
        {
          build_arch: build_arch,
          gh_pr: 'pull_request' in payload.issue ? payload.issue.number : null,
          gh_issue: 'pull_request' in payload.issue ? null : payload.issue.number,
          build_package: build_package,
          repo: `${context.repo().owner}/${context.repo().repo}`,
          action: action,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            token: process.env.JENKINS_WEBHOOK_SECRET,
          },
        },
      );

      context.log.info(`Received jenkins response: ${JSON.stringify(data)}`);

      if (status === 200 && data.jobs['slackbuilds.org-pr-check-build-package'].triggered) {
        context.log.info('Build was successfully scheduled.');
        await context.octokit.reactions.createForIssueComment({
          owner: context.repo().owner,
          repo: context.repo().repo,
          comment_id: payload.comment.id,
          content: '+1',
        });
        context.log.info('Confirmed build triggering by thumbs-upping comment.');
      } else {
        context.log.info('No job triggered.');
      }
    } else {
      context.log.info(
        `Triggering ${action} of package ${build_package} for both i586 and x86_64.`,
      );

      const { data, status } = await axios.post(
        process.env.JENKINS_WEBHOOK,
        {
          build_arch: 'i586',
          gh_pr: payload.issue.pull_request ? payload.issue.number : null,
          gh_issue: payload.issue.pull_request ? null : payload.issue.number,
          build_package: build_package,
          repo: `${context.repo().owner}/${context.repo().repo}`,
          action: action,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            token: process.env.JENKINS_WEBHOOK_SECRET,
          },
        },
      );

      context.log.info(`Received jenkins response for i586 trigger: ${JSON.stringify(data)}`);

      if (status === 200 && data.jobs['slackbuilds.org-pr-check-build-package'].triggered) {
        context.log.info('Build (i586) was successfully scheduled.');

        const { data, status } = await axios.post(
          process.env.JENKINS_WEBHOOK,
          {
            build_arch: 'x86_64',
            gh_pr: payload.issue.pull_request ? payload.issue.number : null,
            gh_issue: payload.issue.pull_request ? null : payload.issue.number,
            build_package: build_package,
            repo: `${context.repo().owner}/${context.repo().repo}`,
            action: action,
          },
          {
            headers: {
              'Content-Type': 'application/json',
              token: process.env.JENKINS_WEBHOOK_SECRET,
            },
          },
        );

        context.log.info(`Received jenkins response for x86_64 trigger: ${JSON.stringify(data)}`);

        if (status === 200 && data.jobs['slackbuilds.org-pr-check-build-package'].triggered) {
          context.log.info('Build (x86_64) was successfully scheduled.');
          await context.octokit.reactions.createForIssueComment({
            owner: context.repo().owner,
            repo: context.repo().repo,
            comment_id: payload.comment.id,
            content: '+1',
          });
          context.log.info('Confirmed build triggerings by thumbs-upping comment.');
        } else {
          context.log.info('No second job triggered.');
        }
      } else {
        context.log.info('No job triggered.');
      }
    }
  });
};
