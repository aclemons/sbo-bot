from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_ssm.client import SSMClient
    from mypy_boto3_ssm.type_defs import GetParameterResultTypeDef, ParameterTypeDef


def run() -> None:
    session = boto3.session.Session()

    client = None
    try:
        client: SSMClient | None = session.client("ssm")

        if not client:
            msg = "Could not create SSM client"
            raise ValueError(msg)

        response: GetParameterResultTypeDef = client.get_parameter(
            Name="/sbobot/gitlab-webhook/env", WithDecryption=True
        )
        parameter: ParameterTypeDef = response.get("Parameter")

        if value := parameter.get("Value"):
            with Path("/tmp/.env").open(mode="w", encoding="utf-8") as f:  # noqa: S108
                f.write(value)
        else:
            sys.exit(1)

    finally:
        if client is not None:
            client.close()
