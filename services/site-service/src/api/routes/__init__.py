"""Сборка роутеров сервиса под общим префиксом.

Префикс /api/v1/site одинаков снаружи и внутри контейнера: gateway проксирует
без переписывания пути (ADR-0009). Ресурсы подключаются сюда по мере готовности:
снимки — B-02, сессии — B-03.
"""

from fastapi import APIRouter, Depends

from src.api.deps import require_api_key

api_router = APIRouter(prefix="/api/v1/site", dependencies=[Depends(require_api_key)])
