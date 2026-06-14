from typing import TYPE_CHECKING, cast

from fastapi import Depends, Request

if TYPE_CHECKING:
    import gitlab
    from aiohttp import ClientSession
    from pyforgejo import AsyncPyforgejoApi

    from sbobot.config import JenkinsConfiguration
    from sbobot.parser import PayloadParserProtocol
    from sbobot.state import State


async def get_state(request: Request) -> "State":
    return cast("State", request.state)


async def get_aiohttp_session(
    state: "State" = Depends(get_state),
) -> "ClientSession":
    return state["aiohttp_session"]


async def get_codeberg(
    state: "State" = Depends(get_state),
) -> "AsyncPyforgejoApi":
    return state["codeberg"]


async def get_codeberg_payload_parser(
    state: "State" = Depends(get_state),
) -> "PayloadParserProtocol":
    return state["codeberg_payload_parser"]


async def get_codeberg_token(state: "State" = Depends(get_state)) -> "str":
    return state["codeberg_token"]


async def get_gitlab(state: "State" = Depends(get_state)) -> "gitlab.Gitlab":
    return state["gitlab"]


async def get_gitlab_payload_parser(
    state: "State" = Depends(get_state),
) -> "PayloadParserProtocol":
    return state["gitlab_payload_parser"]


async def get_gitlab_token(state: "State" = Depends(get_state)) -> "str":
    return state["gitlab_token"]


async def get_jenkins_configuration(
    state: "State" = Depends(get_state),
) -> "JenkinsConfiguration":
    return state["jenkins_configuration"]
