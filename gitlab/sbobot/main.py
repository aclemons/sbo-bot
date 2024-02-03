import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse


def build_uvicorn_app() -> FastAPI:
    from api import healthcheck_router, webhook_router

    app = FastAPI(
        default_response_class=ORJSONResponse,
        separate_input_output_schemas=False,
        title="sbo-bot Gitlab Webhook",
        description="Webhook for events from slackbuilds.org gitlab.",
        contact={"name": "SBo Admins"},
        version="0.0.0",
        responses={},
        debug=False,
        lifespan=None,
        servers=None,
    )

    app.include_router(healthcheck_router)
    app.include_router(webhook_router)

    return app


if __name__ == "__main__":
    uvicorn.run(
        "main:build_uvicorn_app",
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=8000,
        factory=True,
        forwarded_allow_ips=[],
        server_header=False,
        reload=False,
    )
