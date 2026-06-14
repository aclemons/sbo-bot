import hashlib
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.http import HTTPBearer

from sbobot.deps import get_codeberg_token

if TYPE_CHECKING:
    from fastapi.security.http import HTTPAuthorizationCredentials


async def auth(
    codeberg_token: str = Depends(get_codeberg_token),
    auth_header: "HTTPAuthorizationCredentials" = Security(HTTPBearer(auto_error=True)),  # noqa: B008
) -> None:
    hash_api_key = hashlib.sha512(auth_header.credentials.encode("utf-8")).hexdigest()

    if hash_api_key != codeberg_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid API key",
        )
