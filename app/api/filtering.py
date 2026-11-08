from collections.abc import Collection, Sequence
from typing import Annotated, Any

from fastapi import Query
from sqlalchemy import Select, or_
from sqlalchemy.orm import InstrumentedAttribute

ESCAPE_CHAR = "\\"

SearchQuery = Annotated[
    str | None,
    Query(max_length=100, description="Case-insensitive text search"),
]


def escape_like(value: str) -> str:
    return (
        value.replace(ESCAPE_CHAR, ESCAPE_CHAR * 2)
        .replace("%", f"{ESCAPE_CHAR}%")
        .replace("_", f"{ESCAPE_CHAR}_")
    )


def apply_search(
    stmt: Select[Any],
    q: str | None,
    columns: Sequence[InstrumentedAttribute[Any]],
) -> Select[Any]:
    term = q.strip() if q else ""
    if not term or not columns:
        return stmt
    pattern = f"%{escape_like(term)}%"
    return stmt.where(or_(*(c.ilike(pattern, escape=ESCAPE_CHAR) for c in columns)))


def apply_eq(
    stmt: Select[Any], column: InstrumentedAttribute[Any], value: Any
) -> Select[Any]:
    if value is None:
        return stmt
    return stmt.where(column == value)


def apply_range(
    stmt: Select[Any],
    column: InstrumentedAttribute[Any],
    minimum: Any = None,
    maximum: Any = None,
) -> Select[Any]:
    if minimum is not None:
        stmt = stmt.where(column >= minimum)
    if maximum is not None:
        stmt = stmt.where(column <= maximum)
    return stmt


def apply_in(
    stmt: Select[Any],
    column: InstrumentedAttribute[Any],
    values: Collection[Any] | None,
) -> Select[Any]:
    if not values:
        return stmt
    return stmt.where(column.in_(values))
