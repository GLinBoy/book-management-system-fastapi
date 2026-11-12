from collections.abc import Callable, Mapping
from typing import Annotated, Any

from fastapi import Query
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

SortAllowlist = Mapping[str, InstrumentedAttribute[Any]]


def parse_sort(
    raw: str,
    allowed: SortAllowlist,
    *,
    nulls_last: bool = False,
) -> list[ColumnElement[Any]]:
    orders: list[ColumnElement[Any]] = []
    seen: set[str] = set()
    for token in (part.strip() for part in raw.split(",")):
        if not token:
            continue
        descending = token.startswith("-")
        name = token[1:] if descending else token
        if name not in allowed:
            raise RequestValidationError(
                [
                    {
                        "type": "value_error",
                        "loc": ("query", "sort"),
                        "msg": (
                            f"Unknown sort field '{name}'. "
                            f"Allowed: {', '.join(sorted(allowed))}"
                        ),
                        "input": raw,
                    }
                ]
            )
        if name in seen:
            continue
        seen.add(name)
        column = allowed[name]
        order = column.desc() if descending else column.asc()
        if nulls_last:
            order = order.nulls_last()
        orders.append(order)
    return orders


def sort_dependency(
    allowed: SortAllowlist,
    *,
    default: str,
    tiebreaker: InstrumentedAttribute[Any] | None = None,
    nulls_last: bool = False,
) -> Callable[..., list[ColumnElement[Any]]]:
    description = (
        "Comma-separated fields; prefix with - for descending. "
        f"Allowed: {', '.join(sorted(allowed))}. Default: {default}."
    )

    def dependency(
        sort: Annotated[str | None, Query(description=description)] = None,
    ) -> list[ColumnElement[Any]]:
        orders = parse_sort(
            sort or default,
            allowed,
            nulls_last=nulls_last,
        )
        if tiebreaker is not None:
            orders.append(tiebreaker.asc())
        return orders

    return dependency
