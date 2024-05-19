import asyncio
import os
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import APIRouter, Depends, status

from sbobot.auth import auth
from sbobot.deps import (
    get_aiohttp_session,
    get_gitlab,
    get_jenkins_configuration,
    get_payload_parser,
)

if TYPE_CHECKING:
    import gitlab
    from aiohttp import ClientSession

    from sbobot.config import JenkinsConfiguration
    from sbobot.parser import PayloadParserProtocol

webhook_router = APIRouter(tags=["webhook"])

ALLOWED_COMMENTORS = (os.environ.get("GITLAB_ADMINS") or "").split(",")

log = structlog.get_logger()


@webhook_router.post(
    "/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth)],
)
async def webhook(
    payload: dict[str, Any],
    gitlab: "gitlab.Gitlab" = Depends(get_gitlab),
    http_client: "ClientSession" = Depends(get_aiohttp_session),
    jenkins_configuration: "JenkinsConfiguration" = Depends(get_jenkins_configuration),
    payload_parser: "PayloadParserProtocol" = Depends(get_payload_parser),
) -> None:
    log.info("Processing incoming webhook payload", payload=payload)

    command = payload_parser.parse(payload)

    if command is None:
        log.info("Payload was not a command.")
        return

    if command.commentator not in ALLOWED_COMMENTORS:
        log.info("Comment was not made by an admin.")
        return

    mr = gitlab.projects.get(command.project_id, lazy=True).mergerequests.get(
        command.mr_id, lazy=True
    )
    note = mr.notes.get(command.comment_id, lazy=True)

    async def schedule_job(build_arch: str) -> bool:
        log.info(
            "Triggering job for package",
            action=command.command,
            package=command.target,
            arch=build_arch,
        )

        request_data = {
            "build_arch": build_arch,
            "gl_mr": command.mr_id,
            "build_package": command.target,
            "action": command.command,
            "repo": command.repo,
        }

        response = await http_client.post(
            url=jenkins_configuration.webhook_url,
            json=request_data,
            headers={"token": jenkins_configuration.webhook_secret},
        )
        data = await response.json()

        log.info(
            "Received jenkins response",
            action=command.command,
            package=command.target,
            arch=build_arch,
            request=request_data,
            data=data,
        )

        if (
            response.status == status.HTTP_200_OK
            and data["jobs"]["slackbuilds.org-pr-check-build-package"]["triggered"]
        ):
            log.info(
                "Build was successfully scheduled.",
                action=command.command,
                package=command.target,
                arch=build_arch,
            )

            return True

        log.info(
            "No job triggered.",
            action=command.command,
            package=command.target,
            arch=build_arch,
        )
        return False

    tasks: list[asyncio.Task[bool]] = []
    for build_arch in command.arches:
        task = asyncio.create_task(schedule_job(build_arch))
        tasks.append(task)

    success_count = 0
    if tasks:
        done, _ = await asyncio.wait(tasks)

        for task in done:
            if exc := task.exception():
                raise exc

            if task.result():
                success_count += 1

    if success_count == len(command.arches):
        note.awardemojis.create({"name": "thumbsup"})

        log.info("Confirmed build triggering by thumbs-upping comment.")
