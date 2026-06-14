from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TypedDict

    import gitlab
    from aiohttp import ClientSession
    from pyforgejo import AsyncPyforgejoApi

    from sbobot.config import JenkinsConfiguration
    from sbobot.parser import PayloadParserProtocol

    class State(TypedDict):
        aiohttp_session: "ClientSession"
        codeberg: "AsyncPyforgejoApi"
        codeberg_payload_parser: "PayloadParserProtocol"
        codeberg_token: str
        gitlab: "gitlab.Gitlab"
        gitlab_payload_parser: "PayloadParserProtocol"
        gitlab_token: str
        jenkins_configuration: "JenkinsConfiguration"
