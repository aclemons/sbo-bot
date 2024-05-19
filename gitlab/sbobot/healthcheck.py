from fastapi import APIRouter, status

healthcheck_router = APIRouter(tags=["healthcheck"])


@healthcheck_router.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz() -> str:
    return "OK"
