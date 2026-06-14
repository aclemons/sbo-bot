from typing import Any

import pytest

from sbobot.parser import BuildCommand
from sbobot.parser.codeberg import PayloadParser


def test_non_comment_event() -> None:
    payload = {"key": "value"}

    command = PayloadParser().parse(payload)

    assert command is None


@pytest.mark.parametrize(
    ("comment", "expected_command", "target_type"),
    [
        ("test test", None, "issue"),
        ("test test", None, "pull_request_from_issue_comment"),
        (
            "/sbo-bot: build system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=None,
                issue_id=456,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "issue",
        ),
        (
            "@sbo-bot: build i586 system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["i586"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "pull_request_from_issue_comment",
        ),
        (
            "@sbo-bot: rebuild arm system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["arm"],
                target="system/fzf",
                command="rebuild",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "pull_request_from_issue_comment",
        ),
        (
            "@sbo-bot: lint x86_64 system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["x86_64"],
                target="system/fzf",
                command="lint",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "pull_request_from_issue_comment",
        ),
    ],
)
def test_issue_comment_payloads(
    comment: str,
    expected_command: BuildCommand | None,
    target_type: str,
) -> None:
    payload = build_issue_comment_payload(
        comment=comment,
        is_pull_request=target_type == "pull_request_from_issue_comment",
    )

    command = PayloadParser().parse(payload)

    assert command == expected_command

    if expected_command is not None:
        payload["sender"]["id"] = 1

        command = PayloadParser().parse(payload)
        assert command
        assert command.commentator_is_owner is False


def test_pull_request_comment_payload() -> None:
    payload = {
        "action": "created",
        "comment": {
            "id": 123,
            "body": "@sbo-bot: build amd64 system/fzf",
        },
        "pull_request": {
            "number": 456,
            "user": {"id": 123, "login": "testuser1"},
        },
        "repository": {
            "id": 1309714,
            "full_name": "SlackBuilds.org/slackbuilds",
        },
        "sender": {"id": 123, "login": "testuser1"},
    }

    command = PayloadParser().parse(payload)

    assert command == BuildCommand(
        commentator_is_owner=True,
        commentator="testuser1",
        comment_id=123,
        mr_id=456,
        issue_id=None,
        project_id=1309714,
        arches=["x86_64"],
        target="system/fzf",
        command="build",
        repo="SlackBuilds.org/slackbuilds",
    )


def build_issue_comment_payload(
    *, comment: str, is_pull_request: bool
) -> dict[str, Any]:
    issue_data: dict[str, Any] = {
        "number": 456,
        "user": {"id": 123, "login": "testuser1"},
    }

    if is_pull_request:
        issue_data["pull_request"] = {
            "url": "https://codeberg.org/api/v1/repos/123/pulls/456"
        }

    return {
        "action": "created",
        "comment": {
            "id": 123,
            "body": comment,
        },
        "issue": issue_data,
        "repository": {
            "id": 1309714,
            "full_name": "SlackBuilds.org/slackbuilds",
        },
        "sender": {"id": 123, "login": "testuser1"},
    }
