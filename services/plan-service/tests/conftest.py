"""Общие фикстуры.

API-тесты требуют настоящий PostgreSQL (docs/testing.md, п. 5): JSONB и CHECK
на SQLite не воспроизводятся, а тестировать на другой СУБД, чем в проде, —
способ узнать о проблеме в самый неподходящий момент.

Базы нет — API-тесты пропускаются с понятным сообщением, а не падают:
unit-тесты на core/ должны проходить всегда и без докера.
"""

import os
from collections.abc import AsyncIterator

import pytest

# Зависимости API-тестов (httpx, sqlalchemy) импортируются внутри фикстур,
# а не здесь: unit-тесты на core/ обязаны запускаться без окружения сервиса —
# это и есть смысл правила «доменная логика не знает про БД и сеть».

TEST_DSN = os.getenv(
    "PLAN_DB_TEST_DSN",
    "postgresql+asyncpg://plan_user:plan-change-me@localhost:5432/plandb",
)


@pytest.fixture
async def engine() -> AsyncIterator:
    from lct_common.db import create_engine
    from sqlalchemy import text

    from src.dal.models import Base

    engine = create_engine(TEST_DSN)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        await engine.dispose()
        pytest.skip("нужен PostgreSQL: make up postgres (или задайте PLAN_DB_TEST_DSN)")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncIterator:
    """Сессия в транзакции с откатом: тесты не видят изменений друг друга."""
    from sqlalchemy.ext.asyncio import AsyncSession

    connection = await engine.connect()
    transaction = await connection.begin()
    db_session = AsyncSession(bind=connection, expire_on_commit=False)

    yield db_session

    await db_session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
async def client(session) -> AsyncIterator:
    """HTTP-клиент поверх приложения, с подменённой сессией и рабочим ключом."""
    from httpx import ASGITransport, AsyncClient

    from src.api.deps import get_session
    from src.config import settings
    from src.main import app

    async def _session_override() -> AsyncIterator:
        yield session

    app.dependency_overrides[get_session] = _session_override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": settings.api_key},
    ) as http_client:
        yield http_client

    app.dependency_overrides.clear()
