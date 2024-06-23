from __future__ import annotations

import asyncio
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING, cast

import boto3
import structlog

log = structlog.get_logger()

if TYPE_CHECKING:
    from mypy_boto3_ssm.client import SSMClient
    from mypy_boto3_ssm.type_defs import GetParameterResultTypeDef, ParameterTypeDef


def write_config(client: "SSMClient", target_file: str, parameter_name: str) -> None:  # noqa: UP037
    log.info("Fetching env from ssm")

    parameter: ParameterTypeDef | None = None

    try:
        response: GetParameterResultTypeDef = client.get_parameter(
            Name=parameter_name, WithDecryption=True
        )
        parameter = response.get("Parameter")

    except client.exceptions.ParameterNotFound:
        msg = "No env file defined in SSM"
        log.info(msg)

    with Path(target_file).open(mode="wt", encoding="utf-8") as f:
        if parameter is None:
            log.info("Writing empty file", target=target_file)
            f.write("")
        elif value := parameter.get("Value"):
            log.info("Parameter found, writing file", target=target_file)
            f.write(value)
        else:
            msg = "Parameter value was empty"
            log.warning(msg)
            raise ValueError(msg)


async def amain() -> None:
    with closing(cast("SSMClient", boto3.session.Session().client("ssm"))) as client:
        write_config(
            client=client,
            parameter_name="/sbobot/gitlab-webhook/env",
            target_file="/tmp/.env",  # noqa: S108
        )


if __name__ == "__main__":
    asyncio.run(amain())
