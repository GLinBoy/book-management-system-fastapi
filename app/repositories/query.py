from collections.abc import Collection, Sequence
from typing import Any

from sqlalchemy import Select, or_
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

ESCAPE_CHAR = "\\"

FilterClause = ColumnElement[bool]


def escape_like(value: str) -> str:
    return (
        value.replace(ESCAPE_CHAR, ESCAPE_CHAR * 2)
        .replace("%", f"{ESCAPE_CHAR}%")
        .replace("_", f"{ESCAPE_CHAR}_")
    )


def search_filter(
    q: str | None,
    columns: Sequence[InstrumentedAttribute[Any]],
) -> FilterClause | None:
    term = q.strip() if q else ""
    if not term or not columns:
        return None
    pattern = f"%{escape_like(term)}%"
    return or_(*(c.ilike(pattern, escape=ESCAPE_CHAR) for c in columns))


def eq_filter(
    column: InstrumentedAttribute[Any],
    value: Any,
) -> FilterClause | None:
    if value is None:
        return None
    return column == value


def range_filters(
    column: InstrumentedAttribute[Any],
    minimum: Any = None,
    maximum: Any = None,
) -> list[FilterClause]:
    clauses: list[FilterClause] = []
    if minimum is not None:
        clauses.append(column >= minimum)
    if maximum is not None:
        clauses.append(column <= maximum)
    return clauses


def in_filter(
    column: InstrumentedAttribute[Any],
    values: Collection[Any] | None,
) -> FilterClause | None:
    if not values:
        return None
    return column.in_(values)


def apply_search(
    stmt: Select[Any],
    q: str | None,
    columns: Sequence[InstrumentedAttribute[Any]],
) -> Select[Any]:
    clause = search_filter(q, columns)
    return stmt.where(clause) if clause is not None else stmt


def apply_eq(
    stmt: Select[Any], column: InstrumentedAttribute[Any], value: Any
) -> Select[Any]:
    clause = eq_filter(column, value)
    return stmt.where(clause) if clause is not None else stmt


def apply_range(
    stmt: Select[Any],
    column: InstrumentedAttribute[Any],
    minimum: Any = None,
    maximum: Any = None,
) -> Select[Any]:
    return stmt.where(*range_filters(column, minimum, maximum))


def apply_in(
    stmt: Select[Any],
    column: InstrumentedAttribute[Any],
    values: Collection[Any] | None,
) -> Select[Any]:
    clause = in_filter(column, values)
    return stmt.where(clause) if clause is not None else stmt
