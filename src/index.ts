import { Probot } from 'probot';

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

    const { owner, repo } = context.repo();

    // TODO for now we only allow the testing repo.
    if (`${owner}/${repo}` !== 'aclemons/-slackbuilds-test') {
      context.log.info('Comment is not test repo.');
      return;
    }

    if (payload.comment.body.trim().startsWith('@sbo-bot: build')) {
      await context.octokit.reactions.createForIssueComment({owner: context.repo().owner, repo: context.repo().repo, comment_id: payload.comment.id, content: '+1'});
    }
  });
};
