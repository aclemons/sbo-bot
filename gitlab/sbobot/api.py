import os
import re
import sys
from typing import TYPE_CHECKING

import orjson
import structlog
from deps import get_gitlab, get_http_client
from fastapi import APIRouter, Depends, Security, status
from fastapi.security.api_key import APIKeyHeader

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
    "^@sbo-bot: (single-build|build|lint) ((amd64|x86_64|arm|i586) )?([a-zA-z]+\\/[a-zA-Z0-9\\+\\-\\._]+)$"
)

log = structlog.get_logger()


@webhook_router.post(
    "/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(APIKeyHeader(name="x-gitlab-token", auto_error=True))],
)
async def webhook(
    payload: dict,
    gitlab: "gitlab.Gitlab" = Depends(get_gitlab),
    http_client: "ClientSession" = Depends(get_http_client),
) -> None:
    sys.stdout.buffer.write(orjson.dumps(payload, option=orjson.OPT_SORT_KEYS))

    log.info("Processing comment")

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

    action = "lint" if match[1] == "lint" else "build"
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
