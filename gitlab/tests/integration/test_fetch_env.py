from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING, cast

import boto3
import pytest

from sbobot.fetch_env import write_config

if TYPE_CHECKING:
    from collections.abc import Generator

    from mypy_boto3_ssm.client import SSMClient


@pytest.fixture(scope="session")
def ssm_client() -> "Generator[SSMClient, None, None]":
    with closing(cast("SSMClient", boto3.session.Session().client("ssm"))) as client:
        yield client


@pytest.fixture()
def target_file(tmp_path_factory: "pytest.TempPathFactory") -> "Path":
    return tmp_path_factory.mktemp("fetch_env") / ".env"


def test_write_config_no_parameter(
    ssm_client: "SSMClient", target_file: "Path"
) -> None:
    write_config(ssm_client, str(target_file), "/does-not-exist")

    with Path(target_file).open(mode="rt", encoding="utf-8") as f:
        contents = f.read()

        assert contents == ""


def test_write_config_ok(ssm_client: "SSMClient", target_file: "Path") -> None:
    name = "/test-param"
    try:
        ssm_client.put_parameter(
            Name=name, Value="a=b\nc=d\n", Type="SecureString", Overwrite=True
        )
        write_config(ssm_client, str(target_file), name)

        with Path(target_file).open(mode="rt", encoding="utf-8") as f:
            contents = f.read()

            assert contents == "a=b\nc=d\n"
    finally:
        ssm_client.delete_parameters(Names=[name])
