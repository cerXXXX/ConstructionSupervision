"""Зависимости FastAPI: сессия БД, клиенты, проверка ключа."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from lct_common import make_api_key_dependency
from lct_common.db import session_dependency
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.pos_client import PosClient
from src.config import settings

require_api_key = make_api_key_dependency(settings.api_key)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async for session in session_dependency(request.app.state.session_factory):
        yield session


def get_pos_client(request: Request) -> PosClient:
    return request.app.state.pos_client


SessionDep = Annotated[AsyncSession, Depends(get_session)]
PosDep = Annotated[PosClient, Depends(get_pos_client)]
