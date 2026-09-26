"""HTML → PDF (WeasyPrint) и ключ файла отчёта в бакете `reports`.

Ключ детерминирован: `{object_id}/{дата формирования}-{period_from}_{period_to}.pdf`
(architecture.md, 7.2). Повторное формирование того же периода в тот же день заменяет
файл, а не копит копии; список отчётов читается из самого бакета, без таблицы в базе.
"""

import re
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from weasyprint import HTML

KEY_PATTERN = re.compile(
    r"^(?P<object_id>[0-9a-f-]{36})/(?P<generated_on>\d{4}-\d{2}-\d{2})-"
    r"(?P<period_from>\d{4}-\d{2}-\d{2})_(?P<period_to>\d{4}-\d{2}-\d{2})\.pdf$"
)


@dataclass(frozen=True)
class ReportKey:
    object_id: UUID
    generated_on: date
    period_from: date
    period_to: date

    def __str__(self) -> str:
        return (
            f"{self.object_id}/{self.generated_on.isoformat()}-"
            f"{self.period_from.isoformat()}_{self.period_to.isoformat()}.pdf"
        )


def parse_report_key(key: str) -> ReportKey | None:
    """Ключ из бакета → его части; чужой файл в бакете — None, а не ошибка."""
    match = KEY_PATTERN.match(key)
    if match is None:
        return None
    try:
        return ReportKey(
            object_id=UUID(match["object_id"]),
            generated_on=date.fromisoformat(match["generated_on"]),
            period_from=date.fromisoformat(match["period_from"]),
            period_to=date.fromisoformat(match["period_to"]),
        )
    except ValueError:
        return None


def render_pdf(html: str) -> bytes:
    """PDF из готового HTML. Блокирующий вызов: сценарий уводит его в пул потоков.

    Внешних ресурсов у отчёта нет — графики SVG, снимки data URI, шрифт системный, — поэтому
    `base_url` не нужен и WeasyPrint никуда не ходит по сети.
    """
    return HTML(string=html).write_pdf()
