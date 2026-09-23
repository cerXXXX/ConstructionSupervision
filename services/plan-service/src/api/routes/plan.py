"""«Весь план» объекта (межсервисный контракт 1) и импорт графика из файла."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, UploadFile

from src.api.deps import ActorDep, AnalysisDep, SessionDep
from src.api.schemas.plan import Plan, PlanImportResult
from src.services.plan import PlanService
from src.services.plan_import import PlanImportService

router = APIRouter(prefix="/objects/{object_id}/plan", tags=["График"])


@router.get(
    "",
    response_model=Plan,
    summary="Весь план объекта",
    description="Вехи по `seq`, связи, правила, календарь и классы техники одним ответом. "
    "Объект без вех — не ошибка: `stages: []`. Выключенное правило приходит как `rule: null`.",
)
async def get_plan(object_id: UUID, session: SessionDep):
    return await PlanService(session).get_plan(object_id)


@router.post(
    "/import",
    response_model=PlanImportResult,
    summary="Импорт графика из CSV или XLSX",
    description="Столбцы: код, наименование, начало, окончание (обязательно); тип участка, "
    "визуальная стадия, связи (`12.3.1 FS+2`, несколько — через запятую), фаза. Недостающее "
    "берётся из шаблона вехи с тем же кодом, вместе с правилом «веха → техника». График "
    "заменяется целиком; поверх существующего — только с `force=true`. Ошибки — "
    "`PLAN_IMPORT_INVALID` со списком `details.errors` (строка, столбец, текст).",
)
async def import_plan(
    object_id: UUID,
    session: SessionDep,
    signal: AnalysisDep,
    actor: ActorDep,
    file: Annotated[UploadFile, File(description="График: .csv (UTF-8 или cp1251) или .xlsx")],
    force: bool = False,
):
    content = await file.read()
    return await PlanImportService(session, signal).import_file(
        object_id, file.filename or "", content, force=force, actor=actor
    )
