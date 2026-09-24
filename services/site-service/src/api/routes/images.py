"""Приём снимков (F1): пакет из формы и импорт из смонтированной папки."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile, status
from lct_common import ValidationError

from src.api.deps import SessionDep, StorageDep
from src.api.schemas.images import FolderImport, IntakeResult
from src.config import settings
from src.services.images import ImageIntake

router = APIRouter(prefix="/images", tags=["Снимки"])

TIME_NOTE = (
    "Время: EXIF → дата и время в имени файла → поле `captured_at` (ISO-8601; без смещения — "
    "местное время камеры, `CAMERA_TIMEZONE`). Без времени снимок принимается со статусом "
    "`NEEDS_TIME`. Первый снимок камеры становится её эталонным кадром."
)


class BatchTooLarge(ValidationError):
    code = "IMAGE_BATCH_TOO_LARGE"


@router.post(
    "",
    response_model=IntakeResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Загрузить снимки пакетом",
    description=f"До {settings.max_files_per_request} файлов (поле `files`), каждый до "
    f"`MAX_IMAGE_MB`. Камера — поле `camera_code`, иначе подпапка в имени файла "
    f"(`cam-north/20261020_090000.jpg`); новая камера заводится сама. {TIME_NOTE} Ответ — "
    "частичный успех: `accepted` и `rejected`.",
)
async def upload_images(
    session: SessionDep,
    storage: StorageDep,
    object_id: Annotated[UUID, Form()],
    files: Annotated[list[UploadFile], File(description="Снимки: JPEG, PNG, WebP")],
    camera_code: Annotated[str | None, Form()] = None,
    captured_at: Annotated[
        str | None, Form(description="Время съёмки, если его нет в файле")
    ] = None,
):
    if len(files) > settings.max_files_per_request:
        raise BatchTooLarge(
            f"За запрос — не больше {settings.max_files_per_request} файлов",
            limit=settings.max_files_per_request,
            received=len(files),
        )
    batch = [(f.filename or "", await f.read()) for f in files]
    return await ImageIntake(session, storage).upload(
        object_id, batch, camera_code=camera_code, captured_at=captured_at
    )


@router.post(
    "/import",
    response_model=IntakeResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Импорт снимков из смонтированной папки",
    description="Папка `IMPORT_DIR/<path>`: подпапка — код камеры (`cam-north/...`), камеры "
    f"заводятся сами, скрытые файлы пропускаются. {TIME_NOTE} Повторный импорт той же папки "
    "отклоняет уже загруженные снимки как `IMAGE_ALREADY_EXISTS`.",
)
async def import_images(payload: FolderImport, session: SessionDep, storage: StorageDep):
    return await ImageIntake(session, storage).import_folder(payload.object_id, payload.path)
