from typing import Any, Literal

import pytest

from sbobot.parser import BuildCommand, PayloadParser


def test_push_event() -> None:
    payload = {"object_kind": "push"}

    command = PayloadParser().parse(payload)

    assert command is None


@pytest.mark.parametrize(
    ("comment", "expected_command", "event_type"),
    [
        ("test test", None, "Issue"),
        ("test test", None, "MergeRequest"),
        (
            "/sbo-bot: build system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
        ),
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
            "Issue",
        ),
        (
            "/sbo-bot build system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
        ),
        (
            "@sbo-bot: build system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
        ),
        (
            "@sbo-bot build system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
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
            "MergeRequest",
        ),
        (
            "@sbo-bot: build x86_64 system/fzf",
            BuildCommand(
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
            ),
            "MergeRequest",
        ),
        (
            "@sbo-bot: build arm system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["arm"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
        ),
        (
            "@sbo-bot: lint system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="lint",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
        ),
        (
            "@sbo-bot: lint i586 system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["i586"],
                target="system/fzf",
                command="lint",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
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
            "MergeRequest",
        ),
        (
            "@sbo-bot: lint arm system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["arm"],
                target="system/fzf",
                command="lint",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
        ),
        (
            "@sbo-bot: rebuild system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="rebuild",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
        ),
        (
            "@sbo-bot: rebuild i586 system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["i586"],
                target="system/fzf",
                command="rebuild",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
        ),
        (
            "@sbo-bot: rebuild x86_64 system/fzf",
            BuildCommand(
                commentator_is_owner=True,
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                issue_id=None,
                project_id=1309714,
                arches=["x86_64"],
                target="system/fzf",
                command="rebuild",
                repo="SlackBuilds.org/slackbuilds",
            ),
            "MergeRequest",
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
            "MergeRequest",
        ),
    ],
)
def test_comment_issue_or_mr(
    comment: str,
    expected_command: "BuildCommand | None",
    event_type: Literal["Issue", "MergeRequest"],
) -> None:
    comment_id = 123
    noteable_id = 456

    match event_type:
        case "MergeRequest":
            payload: dict[str, Any] = {
                "event_type": "note",
                "object_attributes": {
                    "noteable_type": "MergeRequest",
                    "id": comment_id,
                    "note": comment,
                },
                "object_kind": "note",
                "user": {"username": "testuser1", "id": 123},
                "project_id": 1309714,
                "project": {
                    "id": 1309714,
                    "path_with_namespace": "SlackBuilds.org/slackbuilds",
                },
                "merge_request": {"iid": noteable_id, "author_id": 123},
            }
        case "Issue":
            payload: dict[str, Any] = {
                "event_type": "note",
                "object_attributes": {
                    "noteable_type": "Issue",
                    "id": comment_id,
                    "note": comment,
                },
                "object_kind": "note",
                "user": {"username": "testuser1", "id": 123},
                "project_id": 1309714,
                "project": {
                    "id": 1309714,
                    "path_with_namespace": "SlackBuilds.org/slackbuilds",
                },
                "issue": {"iid": noteable_id, "author_id": 123},
            }

    command = PayloadParser().parse(payload)

    assert command == expected_command

    if expected_command is not None:
        payload["user"]["id"] = 1

        command = PayloadParser().parse(payload)
        assert command
        assert command.commentator_is_owner is False
