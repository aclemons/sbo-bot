from dataclasses import dataclass
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from sbobot.jenkins import schedule_builds
from sbobot.parser import BuildCommand

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sbobot.parser import ArchValue


EXPECTED_ARCH_REQUESTS = 2


@dataclass(frozen=True)
class SuccessCase:
    arches: "list[ArchValue]"
    mr_id: int | None
    issue_id: int | None
    id_keys: tuple[str, str]
    responses: list[tuple[int, bool]]
    expected_success_awaits: int
    payload_index: int
    expected_mr_value: int | None
    expected_issue_value: int | None


SUCCESS_CASES = [
    SuccessCase(
        arches=["i586", "x86_64"],
        mr_id=456,
        issue_id=None,
        id_keys=("gl_mr", "gl_issue"),
        responses=[(200, True), (200, True)],
        expected_success_awaits=1,
        payload_index=0,
        expected_mr_value=456,
        expected_issue_value=None,
    ),
    SuccessCase(
        arches=["i586", "x86_64"],
        mr_id=None,
        issue_id=789,
        id_keys=("cb_pr", "cb_issue"),
        responses=[(200, True), (200, False)],
        expected_success_awaits=0,
        payload_index=1,
        expected_mr_value=None,
        expected_issue_value=789,
    ),
]


def build_command(
    arches: "Sequence[ArchValue]", *, mr_id: int | None, issue_id: int | None
) -> BuildCommand:
    return BuildCommand(
        commentator_is_owner=True,
        commentator="testuser1",
        comment_id=123,
        mr_id=mr_id,
        issue_id=issue_id,
        project_id=1309714,
        arches=list(arches),
        target="system/fzf",
        command="build",
        repo="SlackBuilds.org/slackbuilds",
    )


def build_response(*, status_code: int, triggered: bool) -> AsyncMock:
    response = AsyncMock()
    response.status = status_code
    response.json.return_value = {
        "jobs": {
            "slackbuilds.org-pr-check-build-package": {
                "triggered": triggered,
            },
        },
    }
    return response


@pytest.fixture
def http_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def jenkins_configuration() -> MagicMock:
    config = MagicMock()
    config.webhook_url = "http://jenkins/webhook"
    config.webhook_secret = "secret"  # noqa: S105
    return config


@pytest.fixture
def on_all_success() -> AsyncMock:
    return AsyncMock()


@pytest.mark.parametrize(
    "case",
    SUCCESS_CASES,
)
async def test_schedule_builds_success_behaviour(
    case: SuccessCase,
    http_client: AsyncMock,
    jenkins_configuration: MagicMock,
    on_all_success: AsyncMock,
) -> None:
    command = build_command(
        case.arches,
        mr_id=case.mr_id,
        issue_id=case.issue_id,
    )

    http_client.post.side_effect = [
        build_response(status_code=status_code, triggered=triggered)
        for status_code, triggered in case.responses
    ]

    await schedule_builds(
        command=command,
        http_client=http_client,
        jenkins_configuration=jenkins_configuration,
        id_keys=case.id_keys,
        on_all_success=on_all_success,
    )

    assert on_all_success.await_count == case.expected_success_awaits
    assert http_client.post.await_count == EXPECTED_ARCH_REQUESTS

    payload = http_client.post.await_args_list[case.payload_index].kwargs["json"]
    assert payload[case.id_keys[0]] == case.expected_mr_value
    assert payload[case.id_keys[1]] == case.expected_issue_value


async def test_schedule_builds_propagates_http_client_errors(
    http_client: AsyncMock,
    jenkins_configuration: MagicMock,
    on_all_success: AsyncMock,
) -> None:
    command = build_command(["x86_64"], mr_id=456, issue_id=None)

    http_client.post.side_effect = RuntimeError("network boom")

    with pytest.raises(RuntimeError, match="network boom"):
        await schedule_builds(
            command=command,
            http_client=http_client,
            jenkins_configuration=jenkins_configuration,
            id_keys=("gl_mr", "gl_issue"),
            on_all_success=on_all_success,
        )

    on_all_success.assert_not_awaited()
