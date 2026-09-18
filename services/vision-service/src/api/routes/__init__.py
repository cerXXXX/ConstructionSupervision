"""Сборка роутеров сервиса под общим префиксом.

Префикс /api/v1/vision одинаков снаружи и внутри контейнера: gateway
проксирует без переписывания пути (ADR-0009). Распознавание подключается
сюда задачей B-04.
"""

from fastapi import APIRouter, Depends

from src.api.deps import require_api_key

api_router = APIRouter(prefix="/api/v1/vision", dependencies=[Depends(require_api_key)])
