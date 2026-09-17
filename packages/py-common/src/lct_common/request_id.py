"""Идентификатор запроса: сквозная трассировка через все сервисы.

Приходит из gateway заголовком X-Request-Id, кладётся в contextvar,
попадает в каждую строку логов, в тело ошибки и во все исходящие вызовы.
По нему собирается вся цепочка: docker compose logs | grep <request_id>.
"""

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-Id"

_request_id: ContextVar[str] = ContextVar("request_id", default="")


def current_request_id() -> str:
    """Идентификатор текущего запроса; пустая строка вне обработчика."""
    return _request_id.get()


def set_request_id(value: str) -> None:
    _request_id.set(value)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        set_request_id(request_id)
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
