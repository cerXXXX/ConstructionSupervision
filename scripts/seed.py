"""Заготовка: загрузка демо-данных и прогон анализа."""

import sys

from _common import not_implemented

WHAT = (
    "демо-объект, импорт графика data/seed/schedule.xlsx, камеры и зоны из "
    "data/seed/cameras.json, загрузка снимков, ожидание распознавания, прогон анализа"
)

if __name__ == "__main__":
    sys.exit(not_implemented("seed.py", "T27", WHAT))
