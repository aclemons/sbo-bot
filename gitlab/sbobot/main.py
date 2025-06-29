import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import gitlab
from aiohttp import ClientSession, ClientTimeout
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

import sbobot
from sbobot.api import webhook_router
from sbobot.config import JenkinsConfiguration
from sbobot.healthcheck import healthcheck_router
from sbobot.parser import PayloadParser
from sbobot.state import StateHolder, initialise_app_state

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def build_uvicorn_app() -> "FastAPI":
    @asynccontextmanager
    async def lifespan(app: "FastAPI") -> "AsyncIterator[None]":
        payload_parser = PayloadParser()

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
                payload_parser=payload_parser,
            )

            initialise_app_state(state, app.state)

            # run
            yield

    app = FastAPI(
        default_response_class=ORJSONResponse,
        separate_input_output_schemas=False,
        title="sbo-bot Gitlab Webhook",
        description="Webhook for events from slackbuilds.org gitlab.",
        contact={"name": "SBo Admins"},
        version=sbobot.__version__,
        responses={},
        debug=False,
        lifespan=lifespan,
        servers=None,
    )

    app.include_router(healthcheck_router)
    app.include_router(webhook_router)

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
