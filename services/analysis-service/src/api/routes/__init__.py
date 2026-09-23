"""Сборка роутеров сервиса под общим префиксом.

Префикс /api/v1/analysis одинаков снаружи и внутри контейнера: gateway
проксирует без переписывания пути (ADR-0009). Ресурсы подключаются сюда
по мере готовности.
"""

from fastapi import APIRouter, Depends

from src.api.deps import require_api_key
from src.api.routes import runs

api_router = APIRouter(prefix="/api/v1/analysis", dependencies=[Depends(require_api_key)])
api_router.include_router(runs.router)
