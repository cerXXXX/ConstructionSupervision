"""Привязка детекции к зоне по точке контакта с землёй (F3; methodology.md, раздел 3).

Зона — полигон на кадре камеры, участок — все зоны объекта с одинаковыми типом и названием
(ADR-0013). Координаты нормированы 0…1 от размера кадра, начало — левый верхний угол, ось y
направлена вниз (ADR-0006). Здесь только геометрия: что значит машина на участке, решает
analysis-service (ADR-0012).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from shapely.geometry import Point, Polygon
from shapely.validation import explain_validity

# Детекция вне всех не опасных зон камеры (methodology.md, раздел 2).
OUTSIDE = "OUTSIDE"
# Роль опасной зоны в enums.yaml: zone_type_role. Такая зона накладывается поверх остальных.
SAFETY_ROLE = "SAFETY"
MIN_POINTS = 3

Point2 = tuple[float, float]


class PolygonError(ValueError):
    """Полигон зоны не имеет смысла: такая зона не сохраняется."""


@dataclass(frozen=True)
class ZoneShape:
    """Зона камеры в том виде, который нужен для привязки."""

    id: UUID
    zone_type: str
    name: str
    polygon: tuple[Point2, ...]

    @property
    def area(self) -> str:
        return area_key(self.zone_type, self.name)


@dataclass(frozen=True)
class Placement:
    """Куда попала детекция: основная зона и опасные зоны, в которых лежит точка контакта."""

    anchor: Point2
    zone: ZoneShape | None
    danger: tuple[ZoneShape, ...]

    @property
    def area(self) -> str:
        """Ключ участка основной зоны или OUTSIDE."""
        return self.zone.area if self.zone is not None else OUTSIDE


def area_key(zone_type: str, name: str) -> str:
    """Ключ участка `ТИП:Название` (ADR-0013): одна подпись на разных камерах — один участок."""
    return f"{zone_type}:{name.strip()}"


def check_polygon(points: Any) -> tuple[Point2, ...]:
    """Полигон зоны из JSON: не меньше трёх вершин в пределах кадра, без самопересечений.

    Замыкающую вершину (равную первой) можно не повторять: она убирается.
    """
    try:
        vertices = [(float(x), float(y)) for x, y in points]
    except (TypeError, ValueError) as exc:
        raise PolygonError("Полигон — список точек [x, y] с числами от 0 до 1") from exc
    if len(vertices) > 1 and vertices[0] == vertices[-1]:
        vertices.pop()
    if len(vertices) < MIN_POINTS:
        raise PolygonError(f"В полигоне меньше {MIN_POINTS} вершин")
    outside = [v for v in vertices if not (0 <= v[0] <= 1 and 0 <= v[1] <= 1)]
    if outside:
        raise PolygonError(
            f"Координаты нормированы 0…1 от размера кадра, а не пиксели: {outside[:3]}"
        )
    shape = Polygon(vertices)
    # Вырожденность — по выпуклой оболочке: у «бабочки» площадь полигона тоже нулевая, но
    # она пересекает сама себя, а не лежит на прямой.
    if shape.convex_hull.area == 0:
        raise PolygonError("Полигон вырожден: все вершины на одной линии")
    if not shape.is_valid:
        raise PolygonError(f"Полигон пересекает сам себя: {explain_validity(shape)}")
    return tuple(vertices)


def anchor_point(bbox: Sequence[float]) -> Point2:
    """Середина нижней стороны рамки `[x1, y1, x2, y2]` — точка касания машины с землёй.

    Центр рамки для высокой техники (кран, бетононасос) систематически уводил бы её
    из зоны, где она стоит.
    """
    x1, _, x2, y2 = (float(v) for v in bbox)
    return ((x1 + x2) / 2, y2)


def place(bbox: Sequence[float], zones: Sequence[ZoneShape], roles: Mapping[str, str]) -> Placement:
    """Привязка рамки к активным зонам её камеры.

    Основная зона — самая маленькая по площади не опасная зона, содержащая точку контакта:
    она специфичнее. Точка на границе полигона считается внутри: зоны размечают с запасом.
    Опасные зоны не участвуют в выборе основной и учитываются отдельно (D6).
    """
    anchor = anchor_point(bbox)
    point = Point(anchor)
    containing = [(Polygon(z.polygon), z) for z in zones]
    containing = [(shape, z) for shape, z in containing if shape.covers(point)]
    danger = tuple(z for _, z in containing if roles.get(z.zone_type) == SAFETY_ROLE)
    candidates = [(shape, z) for shape, z in containing if z not in danger]
    # При равной площади — детерминированный выбор по подписи и id, а не по порядку в базе.
    main = min(
        candidates,
        key=lambda item: (item[0].area, item[1].area, str(item[1].id)),
        default=None,
    )
    return Placement(anchor, main[1] if main else None, danger)
