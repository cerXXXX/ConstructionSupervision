"""DTO приёма снимков (api-guidelines.md, раздел 7)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AcceptedImage(BaseModel):
    image_id: UUID
    file: str
    camera_code: str
    captured_at: datetime | None = Field(description="UTC; null — ждёт ручного ввода")
    captured_at_source: str = Field(description="EXIF, FILENAME, MANUAL или UNKNOWN")
    time_detail: str = Field(description="Откуда взято время, словами")
    status: str = Field(description="PENDING — ждёт распознавания, NEEDS_TIME — ждёт времени")


class RejectedImage(BaseModel):
    file: str
    code: str = Field(
        description="IMAGE_ALREADY_EXISTS, IMAGE_TOO_LARGE, UNSUPPORTED_MEDIA_TYPE, "
        "CAMERA_REQUIRED, STORAGE_UNAVAILABLE"
    )
    message: str
    image_id: UUID | None = Field(default=None, description="Для повтора — id уже загруженного")


class IntakeResult(BaseModel):
    """Частичный успех: отклонённый файл — строка в `rejected`, а не ошибка запроса."""

    accepted: list[AcceptedImage]
    rejected: list[RejectedImage]


class FolderImport(BaseModel):
    object_id: UUID
    path: str = Field(
        default="",
        description="Папка внутри IMPORT_DIR; каждая её подпапка — код камеры. Пусто — сам "
        "IMPORT_DIR",
        examples=["", "day1"],
    )
