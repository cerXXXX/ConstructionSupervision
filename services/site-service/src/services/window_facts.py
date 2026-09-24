"""Пересчёт факта окна по его распознанным снимкам и текущей разметке зон (methodology.md, 4.6).

Окно пересчитывается целиком, а не дописывается: поздний снимок, повторное распознавание и
правка зон дают тот же факт, что и обработка всего окна с нуля.
"""

from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.aggregation import CameraZones, Frame, FrameDetection, aggregate_window
from src.core.zones import ZoneShape
from src.dal.repositories.cameras import CameraRepository
from src.dal.repositories.facts import FactRepository
from src.dal.repositories.recognition import RecognitionRepository
from src.dal.repositories.zones import ZoneRepository
from src.reference import enums


class WindowFacts:
    def __init__(self, session: AsyncSession) -> None:
        self._recognition = RecognitionRepository(session)
        self._facts = FactRepository(session)
        self._cameras = CameraRepository(session)
        self._zones = ZoneRepository(session)

    async def recompute(self, session_id: UUID, object_id: UUID) -> None:
        frames = [
            Frame(
                image_id=image.id,
                camera_id=image.camera_id,
                usable=bool(image.usable),
                reason=image.usable_reason,
                detections=tuple(
                    FrameDetection(d.id, d.equipment_class, tuple(d.bbox), d.conf, d.moved)
                    for d in detections
                ),
                stage_scores=stage.scores if stage else None,
            )
            for image, detections, stage in await self._recognition.window_frames(session_id)
        ]
        fact = aggregate_window(frames, await self.cameras(object_id), enums().zone_roles)
        await self._facts.replace_window_fact(session_id, fact)

    async def cameras(self, object_id: UUID) -> list[CameraZones]:
        """Активные камеры объекта с активными зонами; камера без зон нужна для OUTSIDE."""
        zones: dict[UUID, list[ZoneShape]] = defaultdict(list)
        for zone, camera in await self._zones.active_on_active_cameras(object_id):
            zones[camera.id].append(shape(zone))
        return [
            CameraZones(camera.id, camera.code, tuple(zones[camera.id]))
            for camera in await self._cameras.for_object(object_id)
            if camera.is_active
        ]


def shape(zone) -> ZoneShape:
    """Зона из базы в том виде, который нужен для привязки."""
    return ZoneShape(zone.id, zone.zone_type, zone.name, tuple(tuple(p) for p in zone.polygon))
