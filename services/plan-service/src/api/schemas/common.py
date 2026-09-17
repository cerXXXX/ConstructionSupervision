"""Общие элементы контракта. Значения enum — из packages/contracts/enums.yaml."""

from enum import StrEnum


class ObjectType(StrEnum):
    RESIDENTIAL_MONOLITH = "RESIDENTIAL_MONOLITH"
    RESIDENTIAL_PANEL = "RESIDENTIAL_PANEL"
    PUBLIC_BUILDING = "PUBLIC_BUILDING"
    ROAD = "ROAD"


class ObjectLifecycle(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ConstructionPhase(StrEnum):
    PREPARATORY = "PREPARATORY"
    SUBSTRUCTURE = "SUBSTRUCTURE"
    SUPERSTRUCTURE = "SUPERSTRUCTURE"
    ENVELOPE_ROOF = "ENVELOPE_ROOF"
    NETWORKS = "NETWORKS"
    LANDSCAPING = "LANDSCAPING"


class ZoneType(StrEnum):
    PIT = "PIT"
    BUILDING_FOOTPRINT = "BUILDING_FOOTPRINT"
    PERIMETER = "PERIMETER"
    ENTRY_GATE = "ENTRY_GATE"
    STORAGE = "STORAGE"
    DANGER = "DANGER"
    ROAD = "ROAD"
