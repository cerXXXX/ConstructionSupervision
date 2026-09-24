"""Точка входа site-service.

Сервис площадки: камеры, зоны, снимки, сессии наблюдения, детекции техники.
Отвечает на вопрос «что видно», а не «хорошо это или плохо» (F1, F3, F4).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from lct_common import (
    HealthCheck,
    RequestIdMiddleware,
    get_logger,
    install_error_handlers,
    make_health_router,
    setup_logging,
)
from lct_common.db import create_engine, create_session_factory, make_db_check

from src.api.routes import api_router
from src.config import settings
from src.reference import enums

setup_logging(settings.service_name, settings.log_level, pretty=settings.is_dev)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ресурсы, живущие столько же, сколько процесс: пул БД."""
    engine = create_engine(settings.site_db_dsn, echo=settings.db_echo)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    log.info(
        "service.started",
        version=settings.version,
        env=settings.env,
        # enums.yaml уже прочитан при импорте схем: испорченный файл не даёт стартовать.
        zone_types=len(enums().zone_types),
    )
    yield

    await engine.dispose()
    log.info("service.stopped")


app = FastAPI(
    title="site-service",
    version=settings.version,
    description=(
        "Сервис площадки: камеры, зоны, снимки, сессии наблюдения, детекции техники. "
        "Единственный владелец фактических данных о стройке."
    ),
    lifespan=lifespan,
    # В проде интерактивная документация закрыта: наружу её отдаёт gateway.
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
    openapi_url="/api/v1/site/openapi.json",
)

app.add_middleware(RequestIdMiddleware)
install_error_handlers(app)

app.include_router(
    make_health_router(
        settings.service_name,
        settings.version,
        checks=[HealthCheck("db", lambda: make_db_check(app.state.engine)())],
    )
)
app.include_router(api_router)
