"""Запросы к deviation_rule: настройки D1–D10, источник истины после первого старта."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.predicates import DeviationRule
from src.dal.models import DeviationRule as DeviationRuleRow


class RuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def seed_missing(self, rules: Iterable[DeviationRule]) -> None:
        """Добавляет коды, которых ещё нет в таблице; правленые строки не трогает.

        Так новая запись в data/deviation_rules.yaml появляется после перезапуска, а
        пороги, изменённые через API, не затираются значениями по умолчанию.
        """
        values = [
            {
                "code": r.code,
                "predicate": r.predicate,
                "enabled": r.enabled,
                "severity": r.severity,
                "params": r.params,
                "title_template": r.title_template,
                "message_template": r.message_template,
            }
            for r in rules
        ]
        if values:
            await self._session.execute(
                insert(DeviationRuleRow)
                .values(values)
                .on_conflict_do_nothing(index_elements=["code"])
            )

    async def list(self) -> list[DeviationRule]:
        rows = await self._session.scalars(select(DeviationRuleRow).order_by(DeviationRuleRow.code))
        return [
            DeviationRule(
                code=row.code,
                predicate=row.predicate,
                enabled=row.enabled,
                severity=row.severity,
                params=dict(row.params),
                title_template=row.title_template,
                message_template=row.message_template,
            )
            for row in rows
        ]
