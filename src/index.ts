import { Probot } from 'probot';
import axios from 'axios';

const allowedCommentors = (process.env.GITHUB_ADMINS || '').split(",");

export = (app: Probot) => {
  app.on('issue_comment.created', async (context) => {
    context.log.info('Processing comment');

    if (context.isBot) {
      context.log.info('Ignoring bots (and self).');
      return;
    }

    const { payload } = context;

    if (!payload.issue.pull_request) {
      context.log.info('Payload is not a pull request comment.');
      return;
    }

    if (!allowedCommentors.includes(payload.comment.user.login)) {
      context.log.info('Comment was not made by an admin.');
      return;
    }

    if (!process.env.JENKINS_WEBHOOK || !process.env.JENKINS_WEBHOOK_SECRET) {
      context.log.info('Jenkins webhook vars not configured');
      return;
    }

    const comment = payload.comment.body.trim();
    const matches = comment.match("^(@sbo-bot: build) ((amd64|x86_64|arm|i586) )?([a-zA-z]+\\/[a-zA-Z0-9\\+\\-\\._]+)$");

    if (!matches) {
      context.log.info('Comment not a build request.');
      return;
    }

    const build_arch = matches[3];
    const build_package = matches[4];

    if (build_arch) {
      context.log.info(`Triggering build of package ${build_package} with requested arch: ${build_arch}.`);
      const { data, status } = await axios.post(
        process.env.JENKINS_WEBHOOK, { build_arch: build_arch, 'gh_pr': payload.issue.number, build_package: build_package, repo: `${context.repo().owner}/${context.repo().repo}` },
        { headers: { 'Content-Type': 'application/json', token: process.env.JENKINS_WEBHOOK_SECRET } }
      );

      context.log.info(`Received jenkins response: ${JSON.stringify(data)}`);

      if (status === 200 && data["jobs"]["slackbuilds.org-pr-check-build-package"]['triggered']) {
        context.log.info("Build was successfully scheduled.");
        await context.octokit.reactions.createForIssueComment({ owner: context.repo().owner, repo: context.repo().repo, comment_id: payload.comment.id, content: '+1' });
        context.log.info("Confirmed build triggering by thumbs-upping comment.");
      } else {
        context.log.info("No job triggered.");
      }
    } else {
      context.log.info(`Triggering build of package ${build_package} for both i586 and x86_64.`);

      let { data, status } = await axios.post(
        process.env.JENKINS_WEBHOOK, { build_arch: 'i586', 'gh_pr': payload.issue.number, build_package: build_package, repo: `${context.repo().owner}/${context.repo().repo}` },
        { headers: { 'Content-Type': 'application/json', token: process.env.JENKINS_WEBHOOK_SECRET } }
      );

      context.log.info(`Received jenkins response for i586 trigger: ${JSON.stringify(data)}`);

      if (status === 200 && data["jobs"]["slackbuilds.org-pr-check-build-package"]['triggered']) {
        context.log.info("Build (i586) was successfully scheduled.");

        let { data, status } = await axios.post(
          process.env.JENKINS_WEBHOOK, { build_arch: 'x86_64', 'gh_pr': payload.issue.number, build_package: build_package, repo: `${context.repo().owner}/${context.repo().repo}` },
          { headers: { 'Content-Type': 'application/json', token: process.env.JENKINS_WEBHOOK_SECRET } }
        );

        context.log.info(`Received jenkins response for x86_64 trigger: ${JSON.stringify(data)}`);

        if (status === 200 && data["jobs"]["slackbuilds.org-pr-check-build-package"]['triggered']) {
          context.log.info("Build (x86_64) was successfully scheduled.");
          await context.octokit.reactions.createForIssueComment({ owner: context.repo().owner, repo: context.repo().repo, comment_id: payload.comment.id, content: '+1' });
          context.log.info("Confirmed build triggerings by thumbs-upping comment.");
        } else {
          context.log.info("No second job triggered.");
        }
      } else {
        context.log.info("No job triggered.");
      }
    }
  });
};
