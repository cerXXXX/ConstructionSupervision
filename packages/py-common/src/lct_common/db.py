"""Асинхронное подключение к PostgreSQL.

У каждого сервиса своя база и своя роль: межсервисных JOIN-ов не существует
физически (ADR-0003). Здесь только соединение — запросы живут в `src/dal/`.
"""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def create_engine(dsn: str, *, echo: bool = False) -> AsyncEngine:
    """Движок с пулом, пригодным для нескольких реплик сервиса."""
    return create_async_engine(
        dsn,
        echo=echo,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # соединение могло протухнуть, пока сервис простаивал
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def session_dependency(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Сессия на запрос: commit при успехе, rollback при исключении."""
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def make_db_check(engine: AsyncEngine):
    """Проверка доступности БД для /health/ready."""

    async def check() -> None:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    return check
