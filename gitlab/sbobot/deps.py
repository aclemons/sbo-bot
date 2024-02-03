from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    import gitlab
    from aiohttp import ClientSession


async def get_gitlab(request: Request) -> "gitlab.Gitlab":
    return request.app.state.gitlab


async def get_http_client(request: Request) -> "ClientSession":
    return request.app.state.aiohttp_session
