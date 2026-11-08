import math
from typing import Annotated, Any

from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


class PaginationParams:
    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Page number, from 1")] = 1,
        size: Annotated[
            int, Query(ge=1, le=MAX_PAGE_SIZE, description="Items per page")
        ] = DEFAULT_PAGE_SIZE,
    ) -> None:
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


Pagination = Annotated[PaginationParams, Depends()]


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> Page[T]:
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=math.ceil(total / params.size),
        )


def paginate(
    session: Session, stmt: Select[Any], params: PaginationParams
) -> tuple[list[Any], int]:
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = session.execute(count_stmt).scalar_one()
    rows = session.scalars(stmt.offset(params.offset).limit(params.size)).all()
    return list(rows), total
