"""Доменные ошибки и единый конверт ответа.

Правило слоёв: core/ и services/ бросают доменные исключения, api/ не ловит их
руками — перевод в HTTP делают обработчики, зарегистрированные один раз.
Наружу никогда не уходят текст исключения, имена таблиц и содержимое конфигурации.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from lct_common.logging import get_logger
from lct_common.request_id import current_request_id

log = get_logger(__name__)


class DomainError(Exception):
    """Базовая ошибка предметной области.

    Подклассы задают стабильный code и HTTP-статус. Код — часть контракта
    и перечисляется в README сервиса, поэтому переименование кода —
    несовместимое изменение API.
    """

    code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(DomainError):
    code = "NOT_FOUND"
    http_status = 404


class ValidationError(DomainError):
    code = "VALIDATION_FAILED"
    http_status = 400


class ConflictError(DomainError):
    code = "CONFLICT"
    http_status = 409


class UnauthorizedError(DomainError):
    code = "UNAUTHORIZED"
    http_status = 401


class UpstreamError(DomainError):
    """Зависимый сервис недоступен или ответил ошибкой.

    Важно: это честная 503, а не тихая заглушка с пустыми данными. Частичные,
    «додуманные» выводы не создаются никогда.
    """

    code = "UPSTREAM_UNAVAILABLE"
    http_status = 503


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Единый конверт ошибки для всех сервисов."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": current_request_id(),
        }
    }


def install_error_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики так, чтобы наружу шёл только наш конверт."""

    @app.exception_handler(DomainError)
    async def _domain(_request: Request, exc: DomainError) -> JSONResponse:
        if exc.http_status >= 500:
            log.error("error.domain", code=exc.code, message=exc.message, details=exc.details)
        else:
            log.info("error.domain", code=exc.code, message=exc.message, details=exc.details)
        return JSONResponse(
            status_code=exc.http_status,
            content=error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        # Ошибки схемы FastAPI приводим к тому же конверту: у интегратора
        # не должно быть двух разных форматов ошибок.
        return JSONResponse(
            status_code=422,
            content=error_body(
                "SCHEMA_VALIDATION_FAILED",
                "Запрос не прошёл проверку схемы",
                {"fields": [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        codes = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(codes.get(exc.status_code, "HTTP_ERROR"), str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_request: Request, exc: Exception) -> JSONResponse:
        # Стектрейс уходит в лог, наружу — только код и request_id.
        log.exception("error.unhandled", error=type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content=error_body("INTERNAL_ERROR", "Внутренняя ошибка сервиса"),
        )
