import pytest

from sbobot.parser import BuildCommand, PayloadParser


def test_push_event() -> None:
    payload = {"object_kind": "push"}

    command = PayloadParser().parse(payload)

    assert command is None


def test_comment_on_issue() -> None:
    payload = {"object_kind": "note", "object_attributes": {"noteable_type": "Issue"}}

    command = PayloadParser().parse(payload)

    assert command is None


@pytest.mark.parametrize(
    ("comment", "expected_command"),
    [
        ("test test", None),
        (
            "/sbo-bot: build system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "/sbo-bot build system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: build system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot build system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: build i586 system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["i586"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: build x86_64 system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["x86_64"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: build arm system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["arm"],
                target="system/fzf",
                command="build",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: lint system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="lint",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: lint i586 system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["i586"],
                target="system/fzf",
                command="lint",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: lint x86_64 system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["x86_64"],
                target="system/fzf",
                command="lint",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: lint arm system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["arm"],
                target="system/fzf",
                command="lint",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: rebuild system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["i586", "x86_64"],
                target="system/fzf",
                command="rebuild",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: rebuild i586 system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["i586"],
                target="system/fzf",
                command="rebuild",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: rebuild x86_64 system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["x86_64"],
                target="system/fzf",
                command="rebuild",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
        (
            "@sbo-bot: rebuild arm system/fzf",
            BuildCommand(
                commentator="testuser1",
                comment_id=123,
                mr_id=456,
                project_id=1309714,
                arches=["arm"],
                target="system/fzf",
                command="rebuild",
                repo="SlackBuilds.org/slackbuilds",
            ),
        ),
    ],
)
def test_comment_mr(comment: str, expected_command: "BuildCommand") -> None:
    comment_id = 123
    mr_id = 456

    payload = {
        "event_type": "note",
        "object_attributes": {
            "noteable_type": "MergeRequest",
            "id": comment_id,
            "note": comment,
        },
        "object_kind": "note",
        "user": {"username": "testuser1"},
        "project_id": 1309714,
        "project": {
            "id": 1309714,
            "path_with_namespace": "SlackBuilds.org/slackbuilds",
        },
        "merge_request": {"iid": mr_id},
    }

    command = PayloadParser().parse(payload)

    assert command == expected_command
