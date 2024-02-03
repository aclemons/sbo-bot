import sys

import orjson
from fastapi import APIRouter, status

webhook_router = APIRouter(tags=["webhook"])
healthcheck_router = APIRouter(tags=["healthcheck"])


@webhook_router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def webhook(payload: dict) -> None:
    sys.stdout.buffer.write(orjson.dumps(payload, option=orjson.OPT_SORT_KEYS))


@healthcheck_router.post("/healthz", status_code=status.HTTP_200_OK)
async def healthz() -> str:
    return "OK"
