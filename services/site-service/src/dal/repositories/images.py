"""Запросы к таблицам image и session."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.dal.models import Image, ObservationSession


class ImageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_checksum(self, object_id: UUID, checksum: str) -> Image | None:
        return await self._session.scalar(
            select(Image).where(Image.object_id == object_id, Image.checksum == checksum)
        )

    async def add(self, image: Image) -> Image:
        self._session.add(image)
        await self._session.flush()
        return image

    async def session_for_window(self, object_id: UUID, start: datetime, end: datetime) -> UUID:
        """Окно объекта; нет — заводится. Два снимка одного окна не создают два окна."""
        await self._session.execute(
            insert(ObservationSession)
            .values(object_id=object_id, window_start=start, window_end=end)
            .on_conflict_do_nothing(constraint="uq_session_object_window")
        )
        return await self._session.scalar(
            select(ObservationSession.id).where(
                ObservationSession.object_id == object_id,
                ObservationSession.window_start == start,
            )
        )

    async def recount_session(self, session_id: UUID) -> None:
        """Сколько снимков и камер в окне — пересчётом, а не +1: поздний снимок не собьёт счёт."""
        counts = (
            select(
                func.count(Image.id).label("images"),
                func.count(func.distinct(Image.camera_id)).label("cameras"),
            )
            .where(Image.session_id == session_id)
            .subquery()
        )
        await self._session.execute(
            update(ObservationSession)
            .where(ObservationSession.id == session_id)
            .values(
                image_count=select(counts.c.images).scalar_subquery(),
                camera_count=select(counts.c.cameras).scalar_subquery(),
            )
        )
