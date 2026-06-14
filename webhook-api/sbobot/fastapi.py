from typing import TYPE_CHECKING

import orjson
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any

    from starlette.responses import Response


class ORJSONResponse(JSONResponse):
    def render(self, content: "Any") -> bytes:  # noqa: ANN401
        return orjson.dumps(
            content, option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
        )


class ORJSONRequest(Request):
    async def json(self) -> "Any":  # noqa: ANN401
        if not hasattr(self, "_json"):
            self._json = orjson.loads(await self.body())
        return self._json


class ORJSONRoute(APIRoute):
    def get_route_handler(self) -> "Callable[[Request], Coroutine[Any, Any, Response]]":
        route_handler = super().get_route_handler()

        async def orjson_wrapper(request: Request) -> "Response":
            return await route_handler(ORJSONRequest(request.scope, request.receive))

        return orjson_wrapper
