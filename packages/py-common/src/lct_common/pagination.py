"""Единый формат списков: {items, total, limit, offset}."""

from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")

MAX_LIMIT = 200


class PageParams(BaseModel):
    """Параметры выборки. Подключается через Depends()."""

    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = 50
    offset: Annotated[int, Query(ge=0)] = 0


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(description="Всего записей, удовлетворяющих фильтру")
    limit: int
    offset: int

    @classmethod
    def of(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(items=items, total=total, limit=params.limit, offset=params.offset)
