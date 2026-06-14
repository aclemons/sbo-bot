import os
from typing import TYPE_CHECKING, Annotated, Any

import structlog
from fastapi import APIRouter, Depends, Response, status
from pyforgejo.core.api_error import ApiError as PyforgejoApiError

from sbobot.codeberg.auth import auth
from sbobot.deps import (
    get_aiohttp_session,
    get_codeberg,
    get_codeberg_payload_parser,
    get_jenkins_configuration,
)
from sbobot.fastapi import ORJSONRoute
from sbobot.jenkins import schedule_builds
from sbobot.permissions import is_command_authorised

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from pyforgejo import AsyncPyforgejoApi

    from sbobot.config import JenkinsConfiguration
    from sbobot.parser import PayloadParserProtocol

router = APIRouter(tags=["webhook"], route_class=ORJSONRoute)

ALLOWED_COMMENTATORS = (os.environ.get("CODEBERG_ADMINS") or "").split(",")
ALLOWED_CONTRIBUTORS = (os.environ.get("CODEBERG_CONTRIBUTORS") or "").split(",")

log = structlog.get_logger()


@router.post(
    "/codeberg/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth)],
)
async def codeberg_webhook(
    payload: dict[str, Any],
    http_client: Annotated["ClientSession", Depends(get_aiohttp_session)],
    codeberg: Annotated["AsyncPyforgejoApi", Depends(get_codeberg)],
    jenkins_configuration: Annotated[
        "JenkinsConfiguration", Depends(get_jenkins_configuration)
    ],
    payload_parser: Annotated[
        "PayloadParserProtocol", Depends(get_codeberg_payload_parser)
    ],
) -> Response:
    log.info("Processing incoming webhook payload", payload=payload)

    command = payload_parser.parse(payload)

    if command is None:
        log.info("Payload was not a command.")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if not is_command_authorised(
        command=command,
        allowed_commentators=ALLOWED_COMMENTATORS,
        allowed_contributors=ALLOWED_CONTRIBUTORS,
    ):
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def on_all_success() -> None:
        if "/" not in command.repo:
            log.warning(
                "Build succeeded but repo name was not owner/repo.",
                repo=command.repo,
                comment_id=command.comment_id,
            )
            return

        owner, repo = command.repo.split("/", maxsplit=1)

        try:
            await codeberg.issue.post_comment_reaction(
                owner=owner,
                repo=repo,
                id=command.comment_id,
                content="+1",
            )
        except PyforgejoApiError as exc:
            log.warning(
                "Failed to add codeberg thumbs-up reaction.",
                repo=command.repo,
                comment_id=command.comment_id,
                error=str(exc),
            )
            return

        log.info("Confirmed build triggering for codeberg command.")

    await schedule_builds(
        command=command,
        http_client=http_client,
        jenkins_configuration=jenkins_configuration,
        id_keys=("cb_pr", "cb_issue"),
        on_all_success=on_all_success,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
