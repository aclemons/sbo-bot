import hashlib
import os

import structlog
from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

webhook_router = APIRouter(tags=["webhook"])
healthcheck_router = APIRouter(tags=["healthcheck"])

GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")


log = structlog.get_logger()


async def auth(
    api_key: str = Security(APIKeyHeader(name="x-gitlab-token", auto_error=True)),
) -> None:
    if not GITLAB_TOKEN:
        log.warning("No token configured in `GITLAB_TOKEN`. Rejecting request")
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
