import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import gitlab
from aiohttp import ClientSession, ClientTimeout
from fastapi import FastAPI

import sbobot
from sbobot.config import JenkinsConfiguration
from sbobot.fastapi import ORJSONResponse
from sbobot.gitlab.parser import PayloadParser as GitlabPayloadParser
from sbobot.gitlab.route import router as gitlab_router
from sbobot.healthcheck import healthcheck_router
from sbobot.state import StateHolder, initialise_app_state

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


def build_uvicorn_app() -> "FastAPI":
    @asynccontextmanager
    async def lifespan(app: "FastAPI") -> "AsyncGenerator[None, None]":
        gitlab_payload_parser = GitlabPayloadParser()

        gitlab_client = gitlab.Gitlab(
            private_token=os.environ["GITLAB_AUTH_TOKEN"],
            url=os.environ.get("GITLAB_URL") or None,
        )
        gitlab_token = os.environ["GITLAB_TOKEN"]
        jenkins_configuration = JenkinsConfiguration(
            webhook_url=os.environ["JENKINS_WEBHOOK"],
            webhook_secret=os.environ["JENKINS_WEBHOOK_SECRET"],
        )

        async with ClientSession(timeout=ClientTimeout(total=10)) as aiohttp_session:
            state = StateHolder(
                aiohttp_session=aiohttp_session,
                gitlab=gitlab_client,
                gitlab_token=gitlab_token,
                jenkins_configuration=jenkins_configuration,
                gitlab_payload_parser=gitlab_payload_parser,
            )

            initialise_app_state(state, app.state)

            # run
            yield

    app = FastAPI(
        default_response_class=ORJSONResponse,
        separate_input_output_schemas=False,
        title="sbo-bot Webhook API",
        description="Handle webhook api calls for events for slackbuilds.org repos.",
        contact={"name": "SBo Admins"},
        version=sbobot.__version__,
        responses={},
        debug=False,
        lifespan=lifespan,
        servers=None,
    )

    app.include_router(healthcheck_router)
    app.include_router(gitlab_router)

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "sbobot.main:build_uvicorn_app",
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=8000,
        factory=True,
        forwarded_allow_ips=[],
        server_header=False,
        reload=False,
    )
