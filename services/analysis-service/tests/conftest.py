"""Общие фикстуры.

Тесты схемы требуют настоящий PostgreSQL (docs/testing.md, п. 5): JSONB и CHECK
на SQLite не воспроизводятся, а тестировать на другой СУБД, чем в проде, —
способ узнать о проблеме в самый неподходящий момент.

Базы нет — такие тесты пропускаются с понятным сообщением, а не падают:
unit-тесты на core/ должны проходить всегда и без докера.
"""

import os
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
