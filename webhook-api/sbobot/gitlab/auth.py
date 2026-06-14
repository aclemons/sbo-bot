import hashlib

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from sbobot.deps import get_gitlab_token


async def auth(
    gitlab_token: str = Depends(get_gitlab_token),
    api_key: str = Security(APIKeyHeader(name="x-gitlab-token", auto_error=True)),
) -> None:
    hash_api_key = hashlib.sha512(api_key.encode("utf-8")).hexdigest()

    if hash_api_key != gitlab_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid API key",
        )
