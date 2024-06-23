from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING, cast

import boto3
import pytest

from sbobot.fetch_env import run

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


def test_run_no_parameter(ssm_client: "SSMClient", target_file: "Path") -> None:
    run(ssm_client, str(target_file), "/does-not-exist")

    with Path(target_file).open(mode="rt", encoding="utf-8") as f:
        contents = f.read()

        assert contents == ""
