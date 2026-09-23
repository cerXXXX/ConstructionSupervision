"""Зависимости FastAPI: сессия БД, клиент сигнала в analysis, проверка ключа."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from lct_common import make_api_key_dependency
from lct_common.db import session_dependency
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.analysis_client import AnalysisClient
from src.config import settings

require_api_key = make_api_key_dependency(settings.api_key)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async for session in session_dependency(request.app.state.session_factory):
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_analysis_client(request: Request) -> AnalysisClient:
    return request.app.state.analysis_client


AnalysisDep = Annotated[AnalysisClient, Depends(get_analysis_client)]
