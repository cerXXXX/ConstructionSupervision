"""Точка входа vision-service.

Распознавание на снимке: детекция техники, стадия объекта, качество кадра
(F2, F6). Сервис ничего не знает о предметной области и не хранит состояние —
это чистая функция «картинка → факты о картинке», масштабируемая репликами.
"""

from fastapi import FastAPI
from lct_common import (
    RequestIdMiddleware,
    get_logger,
    install_error_handlers,
    make_health_router,
    setup_logging,
)

from src.api.routes import api_router
from src.config import settings

setup_logging(settings.service_name, settings.log_level, pretty=settings.is_dev)
log = get_logger(__name__)

app = FastAPI(
    title="vision-service",
    version=settings.version,
    description=(
        "Сервис компьютерного зрения: детекция строительной техники, стадия объекта "
        "по внешнему виду и оценка качества кадра. Состояния и зависимостей нет."
    ),
    # В проде интерактивная документация закрыта: наружу её отдаёт gateway.
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
    openapi_url="/api/v1/vision/openapi.json",
)

app.add_middleware(RequestIdMiddleware)
install_error_handlers(app)

# Проверок зависимостей нет: у сервиса их не существует. Готовность станет
# содержательной вместе с загрузкой моделей — /health/ready начнёт отвечать
# ok только после того, как веса окажутся в памяти (B-04).
app.include_router(make_health_router(settings.service_name, settings.version))
app.include_router(api_router)
