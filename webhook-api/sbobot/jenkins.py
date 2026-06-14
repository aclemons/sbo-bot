import asyncio
from typing import TYPE_CHECKING

import structlog
from fastapi import status

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiohttp import ClientSession

    from sbobot.config import JenkinsConfiguration
    from sbobot.parser import BuildCommand

log = structlog.get_logger()


async def schedule_builds(
    *,
    command: "BuildCommand",
    http_client: "ClientSession",
    jenkins_configuration: "JenkinsConfiguration",
    id_keys: tuple[str, str],
    on_all_success: "Callable[[], Awaitable[None]]",
) -> None:
    mr_key, issue_key = id_keys

    async def schedule_job(build_arch: str) -> bool:
        log.info(
            "Triggering job for package",
            action=command.command,
            package=command.target,
            arch=build_arch,
        )

        request_data = {
            "build_arch": build_arch,
            mr_key: None if command.mr_id is None else command.mr_id,
            issue_key: None if command.issue_id is None else command.issue_id,
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
        await on_all_success()
