import os
import sys

import orjson
import structlog
from fastapi import APIRouter, Security, status
from fastapi.security.api_key import APIKeyHeader

webhook_router = APIRouter(tags=["webhook"])
healthcheck_router = APIRouter(tags=["healthcheck"])

GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")


log = structlog.get_logger()


@webhook_router.post(
    "/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(APIKeyHeader(name="x-gitlab-token", auto_error=True))],
)
async def webhook(
    payload: dict,
) -> None:
    sys.stdout.buffer.write(orjson.dumps(payload, option=orjson.OPT_SORT_KEYS))


@healthcheck_router.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz() -> str:
    return "OK"
