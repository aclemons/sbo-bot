import os
import re
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, status

from sbobot.auth import auth
from sbobot.deps import get_gitlab, get_http_client

if TYPE_CHECKING:
    import gitlab
    from aiohttp import ClientSession

webhook_router = APIRouter(tags=["webhook"])
healthcheck_router = APIRouter(tags=["healthcheck"])

ALLOWED_COMMENTORS = (os.environ.get("GITLAB_ADMINS") or "").split(",")

GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")

JENKINS_WEBHOOK = os.environ.get("JENKINS_WEBHOOK")
JENKINS_WEBHOOK_SECRET = os.environ.get("JENKINS_WEBHOOK_SECRET")

COMMENT_RE = re.compile(
    "^@sbo-bot: (single-build|rebuild|build|lint) ((amd64|x86_64|arm|i586) )?([a-zA-z]+\\/[a-zA-Z0-9\\+\\-\\._]+)$"
)

log = structlog.get_logger()


@webhook_router.post(
    "/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth)],
)
async def webhook(
    payload: dict,
    gitlab: "gitlab.Gitlab" = Depends(get_gitlab),
    http_client: "ClientSession" = Depends(get_http_client),
) -> None:
    log.info("Processing incoming webhook payload", payload=payload)

    if (
        payload["object_kind"] != "note"
        or payload["object_attributes"]["noteable_type"] != "MergeRequest"
    ):
        log.info("Payload is not a merge request comment.")
        return

    if payload["user"]["username"] not in ALLOWED_COMMENTORS:
        log.info("Comment was not made by an admin.")
        return

    if not JENKINS_WEBHOOK or not JENKINS_WEBHOOK_SECRET:
        log.info("Jenkins webhook vars not configured")
        return

    comment: str = payload["object_attributes"]["note"]

    match = COMMENT_RE.match(comment)

    if not match:
        log.info("Comment not a build request.")
        return

    mr_id = payload["merge_request"]["iid"]
    mr = gitlab.projects.get(payload["project_id"], lazy=True).mergerequests.get(
        mr_id, lazy=True
    )
    note = mr.notes.get(payload["object_attributes"]["id"], lazy=True)

    if match[1] == "lint":
        action = "lint"
    elif match[1] == "rebuild":
        action = "rebuild"
    else:
        action = "build"

    build_arch = match[3]
    build_package = match[4]

    if build_arch:
        log.info(
            "Triggering job for package",
            action=action,
            package=build_package,
            arch=build_arch,
        )

        request_data = {
            "build_arch": build_arch,
            "gl_mr": mr_id,
            "build_package": build_package,
            "action": action,
            "repo": payload["project"]["path_with_namespace"],
        }

        response = await http_client.post(
            url=JENKINS_WEBHOOK,
            json=request_data,
            headers={"token": JENKINS_WEBHOOK_SECRET},
        )
        data = await response.json()

        log.info("Received jenkins response", request=request_data, data=data)

        if (
            response.status == status.HTTP_200_OK
            and data["jobs"]["slackbuilds.org-pr-check-build-package"]["triggered"]
        ):
            log.info("Build was successfully scheduled.")

            note.awardemojis.create({"name": "thumbsup"})

            log.info("Confirmed build triggering by thumbs-upping comment.")
        else:
            log.info("No job triggered.")
    else:
        log.info(
            "Triggering job for package for both i586 and x86_64",
            action=action,
            package=build_package,
        )

        request_data = {
            "build_arch": "i586",
            "gl_mr": mr_id,
            "build_package": build_package,
            "action": action,
            "repo": payload["project"]["path_with_namespace"],
        }

        response = await http_client.post(
            url=JENKINS_WEBHOOK,
            json=request_data,
            headers={"token": JENKINS_WEBHOOK_SECRET},
        )
        data = await response.json()

        log.info(
            "Received jenkins response for i586 trigger",
            request=request_data,
            data=data,
        )

        if (
            response.status == status.HTTP_200_OK
            and data["jobs"]["slackbuilds.org-pr-check-build-package"]["triggered"]
        ):
            log.info("Build (i586) was successfully scheduled.")

            request_data = {
                "build_arch": "x86_64",
                "gl_mr": mr_id,
                "build_package": build_package,
                "action": action,
                "repo": payload["project"]["path_with_namespace"],
            }

            response = await http_client.post(
                url=JENKINS_WEBHOOK,
                json=request_data,
                headers={"token": JENKINS_WEBHOOK_SECRET},
            )
            data = await response.json()

            log.info(
                "Received jenkins response for x86_64 trigger",
                request=request_data,
                data=data,
            )

            if (
                response.status == status.HTTP_200_OK
                and data["jobs"]["slackbuilds.org-pr-check-build-package"]["triggered"]
            ):
                log.info("Build (x86_64) was successfully scheduled.")

                note.awardemojis.create({"name": "thumbsup"})

                log.info("Confirmed build triggerings by thumbs-upping comment.")
            else:
                log.info("No second job triggered.")
        else:
            log.info("No job triggered.")


@healthcheck_router.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz() -> str:
    return "OK"
