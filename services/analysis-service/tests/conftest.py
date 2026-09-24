"""Общие фикстуры.

Тесты схемы требуют настоящий PostgreSQL (docs/testing.md, п. 5): JSONB и CHECK
на SQLite не воспроизводятся, а тестировать на другой СУБД, чем в проде, —
способ узнать о проблеме в самый неподходящий момент.

Базы нет — такие тесты пропускаются с понятным сообщением, а не падают:
unit-тесты на core/ должны проходить всегда и без докера.
"""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
# Справочные файлы: в контейнере — CONTRACTS_DIR, в рабочей копии и CI — packages/contracts.
CONTRACTS_DIR = Path(os.getenv("CONTRACTS_DIR") or SERVICE_ROOT.parents[1] / "packages/contracts")

# Одна переменная на все сервисы: CI не должен знать про каждый в отдельности.
TEST_DSN = os.getenv(
    "TEST_DB_DSN",
    "postgresql+asyncpg://analysis_user:analysis-change-me@localhost:5432/analysisdb",
)


def _database_is_reachable() -> bool:
    import asyncio

    from lct_common.db import create_engine
    from sqlalchemy import text

    async def probe() -> bool:
        engine = create_engine(TEST_DSN)
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except Exception:  # noqa: BLE001 — причина недоступности БД здесь не важна
            return False
        finally:
            await engine.dispose()

    return asyncio.run(probe())


@pytest.fixture(scope="session")
def alembic_config():
    """Конфиг Alembic, нацеленный на тестовую базу.

    Пути абсолютные: тесты запускаются и из каталога сервиса, и из корня репозитория.
    """
    from alembic.config import Config

    config = Config(str(SERVICE_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(SERVICE_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", TEST_DSN)
    return config


@pytest.fixture(scope="session")
def migrated_database(alembic_config) -> str:
    """Схема поднимается миграциями, а не `create_all`.

    Так каждый прогон тестов заодно проверяет, что миграции применяются: иначе
    о сломанном `upgrade` узнают при старте контейнера, а не в CI.

    Фикстура синхронная намеренно: Alembic внутри поднимает свой event loop,
    и вызывать его из уже работающего цикла нельзя.
    """
    from alembic import command

    if not _database_is_reachable():
        pytest.skip("нужен PostgreSQL: make up postgres (или задайте TEST_DB_DSN)")

    command.upgrade(alembic_config, "head")
    return TEST_DSN


@pytest.fixture(scope="session")
def enums():
    """Перечисления из настоящего enums.yaml: тесты сверяются с контрактом, а не с копией."""
    from src.core.enums import load_enums

    return load_enums(CONTRACTS_DIR)


# Все таблицы выводов: прогон пишет своими транзакциями, поэтому API-тесты изолируются
# очисткой, а не откатом транзакции.
TABLES = (
    "analysis_run, deviation, deviation_rule, stage_fact, daily_activity, daily_equipment, "
    "object_status"
)


@pytest.fixture
async def session_factory(migrated_database):
    """Фабрика сессий к чистой тестовой базе."""
    from lct_common.db import create_engine, create_session_factory
    from sqlalchemy import text

    engine = create_engine(migrated_database)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {TABLES}"))
    yield create_session_factory(engine)
    await engine.dispose()


class StubPlanClient:
    """plan-service на фикстуре: отдаёт план или бросает заданную ошибку."""

    def __init__(self) -> None:
        from tests.factories import load_plan

        self.plan = load_plan()
        self.error: Exception | None = None

    async def get_plan(self, object_id):
        if self.error is not None:
            raise self.error
        return self.plan


class StubSiteClient:
    """site-service на фикстуре: запоминает запрошенный период и, как настоящий, отдаёт
    только сессии с началом окна в [from, to) — иначе ошибка в периоде была бы не видна."""

    def __init__(self) -> None:
        self.facts = None
        self.error: Exception | None = None
        self.calls: list[tuple] = []

    async def get_facts(self, object_id, period_from, period_to):
        self.calls.append((object_id, period_from, period_to))
        if self.error is not None:
            raise self.error
        if self.facts is None:
            return None
        sessions = tuple(
            s for s in self.facts.sessions if period_from <= s.window_start < period_to
        )
        return self.facts.model_copy(update={"sessions": sessions})


@pytest.fixture
async def seeded_rules(session_factory) -> None:
    """Правила D1–D10 в таблице, как после старта сервиса."""
    from src.dal.repositories.rules import RuleRepository
    from src.services.runs import default_rules

    async with session_factory() as session, session.begin():
        await RuleRepository(session).seed_missing(default_rules())


@pytest.fixture
def upstream():
    """Заглушки plan и site: внешние сервисы в тестах не вызываются (AGENTS.md, раздел 10)."""
    from types import SimpleNamespace

    return SimpleNamespace(plan=StubPlanClient(), site=StubSiteClient())


@pytest.fixture
async def client(session_factory, upstream, monkeypatch) -> AsyncIterator:
    """HTTP-клиент поверх приложения с тестовой базой, заглушками и рабочим ключом."""
    from httpx import ASGITransport, AsyncClient
    from lct_common.db import session_dependency
    from src.api.deps import get_run_service, get_session, get_site_client
    from src.config import settings
    from src.main import app
    from src.services import runs
    from src.services.runs import RunService

    async def _session_override() -> AsyncIterator:
        async for session in session_dependency(session_factory):
            yield session

    monkeypatch.setattr(settings, "contracts_dir", str(CONTRACTS_DIR))
    runs.enums.cache_clear()
    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[get_site_client] = lambda: upstream.site
    app.dependency_overrides[get_run_service] = lambda: RunService(
        session_factory, upstream.plan, upstream.site
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": settings.api_key},
    ) as http_client:
        yield http_client
    app.dependency_overrides.clear()
    runs.enums.cache_clear()


DEMO_OBJECT_ID = "0f3a6c1e-8d4b-4c2a-9e71-5b0d2f6a8c31"
DEMO_DAYS = ("facts_normal_day.json", "facts_day1.json", "facts_day2.json", "facts_day3.json")


@pytest.fixture
async def analyzed(client, upstream):
    """Демо-объект после прогона по четырём демо-дням (19–22.10)."""
    from tests.factories import load_facts, make_facts

    upstream.site.facts = make_facts(*(s for n in DEMO_DAYS for s in load_facts(n).sessions))
    response = await client.post(
        "/api/v1/analysis/runs", json={"object_id": DEMO_OBJECT_ID}, params={"wait": True}
    )
    assert response.status_code == 200, response.text
