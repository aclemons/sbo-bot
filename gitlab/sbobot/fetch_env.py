from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
import structlog

log = structlog.get_logger()

if TYPE_CHECKING:
    from mypy_boto3_ssm.client import SSMClient
    from mypy_boto3_ssm.type_defs import GetParameterResultTypeDef, ParameterTypeDef


def run() -> None:
    log.info("Fetching env from ssm")

    session = boto3.session.Session()

    client = None
    try:
        client: SSMClient | None = session.client("ssm")

        if not client:
            msg = "Could not create SSM client"
            log.warning(msg)
            raise ValueError(msg)

        response: GetParameterResultTypeDef = client.get_parameter(
            Name="/sbobot/gitlab-webhook/env", WithDecryption=True
        )
        parameter: ParameterTypeDef = response.get("Parameter")

        if value := parameter.get("Value"):
            log.info("Parameter found, writing .env file to /tmp")
            with Path("/tmp/.env").open(mode="wt", encoding="utf-8") as f:  # noqa: S108
                f.write(value)
        else:
            log.info("Parameter value was empty")
            sys.exit(1)

    finally:
        if client is not None:
            client.close()
