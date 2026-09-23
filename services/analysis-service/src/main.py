"""Точка входа analysis-service.

Сервис сверки план-факт: отклонения D1–D10 с объяснением, прогресс, SPI
и прогноз даты окончания (F7, F8, F9). План и факт читаются по API — своими
первичными данными сервис не владеет, его состояние пересчитывается с нуля.
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
from sqlalchemy.exc import SQLAlchemyError

from src.api.routes import api_router
from src.clients.plan_client import PlanClient
from src.clients.site_client import SiteClient
from src.config import settings
from src.dal.repositories.rules import RuleRepository
from src.services.runs import default_rules

setup_logging(settings.service_name, settings.log_level, pretty=settings.is_dev)
log = get_logger(__name__)


def _client(cls, url: str, service: str):
    return cls(
        url,
        service=service,
        api_key=settings.api_key,
        timeout_s=settings.upstream_timeout_s,
        retries=settings.upstream_retries,
    )


async def _seed_rules(factory) -> None:
    """Первый старт: пороги D1–D10 из YAML в deviation_rule; правленые строки не трогаются.

    База может быть ещё не готова — тогда правила заполнит первый прогон, а сервис
    всё равно поднимется: /health/ready честно скажет, что БД недоступна.
    """
    try:
        async with factory() as session, session.begin():
            await RuleRepository(session).seed_missing(default_rules())
    except (OSError, SQLAlchemyError) as exc:
        log.warning("rules.seed_skipped", error=type(exc).__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ресурсы, живущие столько же, сколько процесс: пул БД и клиенты plan и site."""
    engine = create_engine(settings.analysis_db_dsn, echo=settings.db_echo)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.plan_client = _client(PlanClient, settings.plan_url, "plan-service")
    app.state.site_client = _client(SiteClient, settings.site_url, "site-service")
    await _seed_rules(app.state.session_factory)

    log.info("service.started", version=settings.version, env=settings.env)
    yield

    await app.state.plan_client.aclose()
    await app.state.site_client.aclose()
    await engine.dispose()
    log.info("service.stopped")


app = FastAPI(
    title="analysis-service",
    version=settings.version,
    description=(
        "Сервис сверки план-факт: отклонения D1–D10 с объяснением, прогресс, SPI "
        "и прогноз. Каждое число сопровождается фактами, на которых оно построено."
    ),
    lifespan=lifespan,
    # В проде интерактивная документация закрыта: наружу её отдаёт gateway.
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
    openapi_url="/api/v1/analysis/openapi.json",
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
