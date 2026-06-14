from typing import TYPE_CHECKING

import pytest
from structlog.testing import capture_logs

from sbobot.parser import BuildCommand
from sbobot.permissions import is_command_authorised

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def build_command(
    *,
    commentator: str,
    commentator_is_owner: bool,
    mr_id: int | None,
    issue_id: int | None,
) -> BuildCommand:
    return BuildCommand(
        commentator_is_owner=commentator_is_owner,
        commentator=commentator,
        comment_id=123,
        mr_id=mr_id,
        issue_id=issue_id,
        project_id=789,
        arches=["i586", "x86_64"],
        target="system/fzf",
        command="build",
        repo="SlackBuilds.org/slackbuilds",
    )


def simplified_logs(
    logs: "Sequence[Mapping[str, object]]",
) -> list[tuple[str, str | None]]:
    simplified: list[tuple[str, str | None]] = []

    for entry in logs:
        commentator = entry.get("commentator")
        commentator_value = commentator if isinstance(commentator, str) else None
        simplified.append((str(entry["event"]), commentator_value))

    return simplified


def test_mr_comment_by_admin_is_authorised() -> None:
    command = build_command(
        commentator="admin1",
        commentator_is_owner=False,
        mr_id=456,
        issue_id=None,
    )

    with capture_logs() as logs:
        authorised = is_command_authorised(
            command=command,
            allowed_commentators=["admin1"],
            allowed_contributors=["contrib1"],
        )

    assert authorised is True
    assert logs == []


def test_mr_comment_by_contributor_owner_is_authorised() -> None:
    command = build_command(
        commentator="contrib1",
        commentator_is_owner=True,
        mr_id=456,
        issue_id=None,
    )

    with capture_logs() as logs:
        authorised = is_command_authorised(
            command=command,
            allowed_commentators=["admin1"],
            allowed_contributors=["contrib1"],
        )

    assert authorised is True
    assert simplified_logs(logs) == [
        ("Comment was not made by an admin.", "contrib1"),
    ]


def test_mr_comment_by_non_contributor_is_not_authorised() -> None:
    command = build_command(
        commentator="random1",
        commentator_is_owner=True,
        mr_id=456,
        issue_id=None,
    )

    with capture_logs() as logs:
        authorised = is_command_authorised(
            command=command,
            allowed_commentators=["admin1"],
            allowed_contributors=["contrib1"],
        )

    assert authorised is False
    assert simplified_logs(logs) == [
        ("Comment was not made by an admin.", "random1"),
        ("Comment was not made by a contributor.", "random1"),
    ]


def test_mr_comment_by_contributor_non_owner_is_not_authorised() -> None:
    command = build_command(
        commentator="contrib1",
        commentator_is_owner=False,
        mr_id=456,
        issue_id=None,
    )

    with capture_logs() as logs:
        authorised = is_command_authorised(
            command=command,
            allowed_commentators=["admin1"],
            allowed_contributors=["contrib1"],
        )

    assert authorised is False
    assert simplified_logs(logs) == [
        ("Comment was not made by an admin.", "contrib1"),
        ("Comment was not on the contributor's own PR.", "contrib1"),
    ]


def test_issue_comment_by_admin_is_authorised() -> None:
    command = build_command(
        commentator="admin1",
        commentator_is_owner=False,
        mr_id=None,
        issue_id=456,
    )

    with capture_logs() as logs:
        authorised = is_command_authorised(
            command=command,
            allowed_commentators=["admin1"],
            allowed_contributors=["contrib1"],
        )

    assert authorised is True
    assert logs == []


def test_issue_comment_by_non_admin_is_not_authorised() -> None:
    command = build_command(
        commentator="contrib1",
        commentator_is_owner=True,
        mr_id=None,
        issue_id=456,
    )

    with capture_logs() as logs:
        authorised = is_command_authorised(
            command=command,
            allowed_commentators=["admin1"],
            allowed_contributors=["contrib1"],
        )

    assert authorised is False
    assert simplified_logs(logs) == [
        ("Comment was not made by an admin.", "contrib1"),
    ]


def test_invalid_state_raises_value_error() -> None:
    command = build_command(
        commentator="admin1",
        commentator_is_owner=True,
        mr_id=None,
        issue_id=None,
    )

    with capture_logs(), pytest.raises(ValueError, match="Invalid state"):
        is_command_authorised(
            command=command,
            allowed_commentators=["admin1"],
            allowed_contributors=["contrib1"],
        )
