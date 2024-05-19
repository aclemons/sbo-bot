from typing import TYPE_CHECKING

from fastapi import Depends, Request

if TYPE_CHECKING:
    import gitlab
    from aiohttp import ClientSession

    from sbobot.config import JenkinsConfiguration
    from sbobot.parser import PayloadParserProtocol
    from sbobot.state import State


# https://github.com/encode/starlette/discussions/2562
#
# state is not generic, so centralise all usage here to reduce unchecked code.
# Our e2e tests should catch any mistakes, but this also lets lsp etc
# auto-complete the state fields
#
# state.initialise_app_state makes sure we always set all fields
async def get_state(request: Request) -> "State":
    return request.app.state


async def get_aiohttp_session(state: "State" = Depends(get_state)) -> "ClientSession":
    return state.aiohttp_session


async def get_gitlab(state: "State" = Depends(get_state)) -> "gitlab.Gitlab":
    return state.gitlab


async def get_gitlab_token(state: "State" = Depends(get_state)) -> "str":
    return state.gitlab_token


async def get_jenkins_configuration(
    state: "State" = Depends(get_state),
) -> "JenkinsConfiguration":
    return state.jenkins_configuration


async def get_payload_parser(
    state: "State" = Depends(get_state),
) -> "PayloadParserProtocol":
    return state.payload_parser
