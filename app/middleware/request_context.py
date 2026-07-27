from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    incoming_request_id = request.headers.get("X-Request-ID")
    request_id = incoming_request_id if incoming_request_id else str(uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def register_request_context_middleware(app: FastAPI) -> None:
    app.middleware("http")(request_context_middleware)
