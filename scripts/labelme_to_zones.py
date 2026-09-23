"""Заготовка: разметка LabelMe в зоны камер."""

import sys

from _common import not_implemented

WHAT = (
    "разметка LabelMe (метка ТИП:Название) в data/seed/cameras.json с нормированными координатами"
)

if __name__ == "__main__":
    sys.exit(not_implemented("labelme_to_zones.py", "T27", WHAT))
