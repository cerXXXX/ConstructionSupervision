"""Проверки здоровья: /health — процесс жив, /health/ready — готов обслуживать.

Разделение не формальность: compose ждёт готовности через /health/ready,
а /health обязан отвечать быстро и без обращений к зависимостям, иначе
падение БД выглядит как падение сервиса.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from lct_common.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class HealthCheck:
    """Одна проверка зависимости.

    required=False означает «деградация, а не отказ»: сервис продолжает
    обслуживать то, что не зависит от этой зависимости, и остаётся готовым.
    Так падение соседа не выводит из строя того, кто может работать без него.
    """

    name: str
    check: Callable[[], Awaitable[None]]
    required: bool = True


def make_health_router(
    service_name: str, version: str, checks: list[HealthCheck] | None = None
) -> APIRouter:
    router = APIRouter(tags=["health"])
    checks = checks or []

    @router.get("/health", summary="Процесс жив")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": service_name, "version": version}

    @router.get("/health/ready", summary="Готов обслуживать запросы")
    async def ready() -> JSONResponse:
        results: dict[str, str] = {}
        healthy = True
        for item in checks:
            try:
                await item.check()
                results[item.name] = "ok"
            except Exception as exc:  # noqa: BLE001 — статус зависимости важнее её причины
                log.warning("health.check_failed", check=item.name, error=type(exc).__name__)
                results[item.name] = "fail"
                if item.required:
                    healthy = False

        return JSONResponse(
            status_code=200 if healthy else 503,
            content={
                "status": "healthy" if healthy else "degraded",
                "service": service_name,
                "version": version,
                "checks": results,
            },
        )

    return router
