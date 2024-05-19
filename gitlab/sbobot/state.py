from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import gitlab
    import starlette.datastructures
    from aiohttp import ClientSession

    from sbobot.config import JenkinsConfiguration
    from sbobot.parser import PayloadParserProtocol

    class State(Protocol):
        aiohttp_session: "ClientSession"
        gitlab: "gitlab.Gitlab"
        gitlab_token: str
        jenkins_configuration: "JenkinsConfiguration"
        payload_parser: "PayloadParserProtocol"


@dataclass
class StateHolder:
    aiohttp_session: "ClientSession"
    gitlab: "gitlab.Gitlab"
    gitlab_token: str
    jenkins_configuration: "JenkinsConfiguration"
    payload_parser: "PayloadParserProtocol"


# https://github.com/encode/starlette/discussions/2562
#
# This is the pair for deps.get_state. This takes type state object and smears
# all attributes into the untyped starlette state. We then only access the
# untyped object in deps.get_state to reduce the untyped surface.
def initialise_app_state(
    state: "State", starlette_state: "starlette.datastructures.State"
) -> None:
    for prop, value in vars(state).items():
        setattr(starlette_state, prop, value)
