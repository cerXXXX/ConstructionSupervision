"""Сверка найденных отклонений с лентой (docs/methodology.md, раздел 9, правила ленты).

Прогон считает всё с нуля и находит эпизоды — серии сессий, где условие держалось.
Здесь решается, какой строке ленты соответствует эпизод:
- эпизод и строка с тем же ключом и пересекающимся временем — одно и то же отклонение:
  строка обновляется, а не дублируется;
- эпизод закончился до `as_of` — открытая строка получает `RESOLVED`;
- `REJECTED` не открывается заново, пока условие держится непрерывно; новый эпизод
  после перерыва — новое отклонение;
- открытая строка, которой не нашлось эпизода, — условие пропало: `RESOLVED`.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.core.predicates import Finding

NEW, CONFIRMED, REJECTED, RESOLVED = "NEW", "CONFIRMED", "REJECTED", "RESOLVED"
OPEN = frozenset({NEW, CONFIRMED})


@dataclass(frozen=True)
class LedgerRow:
    """Строка ленты в том объёме, что нужен для сверки."""

    id: UUID
    key: tuple
    status: str
    first_seen_at: datetime
    last_seen_at: datetime


@dataclass(frozen=True)
class LedgerPlan:
    """Что сделать с лентой: закрыть, обновить, добавить — именно в этом порядке.

    Порядок важен: открытая строка по ключу единственна (уникальный индекс), поэтому
    устаревшая открытая строка закрывается раньше, чем по тому же ключу откроется новая.
    """

    resolve: tuple[UUID, ...]
    update: tuple[tuple[UUID, Finding, str], ...]
    insert: tuple[tuple[Finding, str], ...]

    @property
    def opened(self) -> int:
        return sum(status == NEW for _, status in self.insert)


def _overlaps(row: LedgerRow, finding: Finding) -> bool:
    return row.first_seen_at <= finding.last_seen_at and finding.first_seen_at <= row.last_seen_at


def reconcile(existing: Sequence[LedgerRow], findings: Iterable[Finding]) -> LedgerPlan:
    """План изменений ленты объекта по эпизодам прогона."""
    by_key: dict[tuple, list[LedgerRow]] = {}
    for row in existing:
        by_key.setdefault(row.key, []).append(row)
    used: set[UUID] = set()
    updates: list[tuple[UUID, Finding, str]] = []
    inserts: list[tuple[Finding, str]] = []
    for finding in sorted(findings, key=lambda f: f.first_seen_at):
        candidates = [
            r for r in by_key.get(finding.key, []) if r.id not in used and _overlaps(r, finding)
        ]
        row = next((r for r in candidates if r.status in OPEN), None) or next(
            iter(candidates), None
        )
        if row is None:
            inserts.append((finding, NEW if finding.active else RESOLVED))
            continue
        used.add(row.id)
        status = row.status
        if not finding.active and status in OPEN:
            status = RESOLVED
        elif finding.active and status == RESOLVED:
            # Эпизод снова держится на as_of (например, дозагрузили снимки): открываем.
            status = NEW
        updates.append((row.id, finding, status))
    # Открытая строка без эпизода — условие пропало. Сюда же попадает старая открытая
    # строка, по ключу которой начался новый эпизод: открытая строка по ключу одна.
    resolve = tuple(r.id for r in existing if r.status in OPEN and r.id not in used)
    return LedgerPlan(resolve=resolve, update=tuple(updates), insert=tuple(inserts))
