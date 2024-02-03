import hashlib
import os
import sys

import orjson
from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

webhook_router = APIRouter(tags=["webhook"])
healthcheck_router = APIRouter(tags=["healthcheck"])

GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")


@webhook_router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def webhook(
    payload: dict,
    api_key: str = Security(APIKeyHeader(name="x-gitlab-token", auto_error=True)),
) -> None:
    if not GITLAB_TOKEN or not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid API key",
        )

    hash_api_key = hashlib.sha512(api_key.encode("utf-8")).hexdigest()

    if hash_api_key != os.environ.get("GITLAB_TOKEN"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid API key",
        )

    sys.stdout.buffer.write(orjson.dumps(payload, option=orjson.OPT_SORT_KEYS))


@healthcheck_router.post("/healthz", status_code=status.HTTP_200_OK)
async def healthz() -> str:
    return "OK"
