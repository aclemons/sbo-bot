from __future__ import annotations

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

    client: SSMClient | None = boto3.session.Session().client("ssm")

    if not client:
        msg = "Could not create SSM client"
        log.warning(msg)
        raise ValueError(msg)

    parameter: ParameterTypeDef | None = None

    try:
        response: GetParameterResultTypeDef = client.get_parameter(
            Name="/sbobot/gitlab-webhook/env", WithDecryption=True
        )
        parameter = response.get("Parameter")

    except client.exceptions.ParameterNotFound:
        msg = "No env file defined in SSM"
        log.info(msg)
    finally:
        client.close()

    with Path("/tmp/.env").open(mode="wt", encoding="utf-8") as f:  # noqa: S108
        if parameter is None:
            log.info("Writing empty .env file to /tmp")
            f.write("")
        elif value := parameter.get("Value"):
            log.info("Parameter found, writing .env file to /tmp")
            f.write(value)
        else:
            msg = "Parameter value was empty"
            log.warning(msg)
            raise ValueError(msg)


if __name__ == "__main__":
    run()
