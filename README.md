# sbo-bot

> Tools for automating for automating SBo submissions.

## Github

A webhook for requesting builds of Github PRs. See [github](github) for details.

## Webhook API

An API for processing webhook requests. See [webhook-api](webhook-api) for
details.

Currently handles:

- [gitlab](https://gitlab.com/SlackBuilds.org/slackbuilds) — requests builds of
  Gitlab MRs.

## Scripts

In [bin](bin), there are some scripts for generating PRs on github or MRs on
gitlab for submission tarballs uploaded on slackbuilds.org.

## License

[MIT](LICENSE) © 2023-2026 Andrew Clemons
