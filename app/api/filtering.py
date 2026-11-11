from typing import Annotated

from fastapi import Query

from app.repositories.query import (
    ESCAPE_CHAR,
    apply_eq,
    apply_in,
    apply_range,
    apply_search,
    escape_like,
)

SearchQuery = Annotated[
    str | None,
    Query(max_length=100, description="Case-insensitive text search"),
]

__all__ = [
    "ESCAPE_CHAR",
    "SearchQuery",
    "apply_eq",
    "apply_in",
    "apply_range",
    "apply_search",
    "escape_like",
]
