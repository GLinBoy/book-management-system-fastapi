import uuid
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.sql.elements import ColumnElement

from app.api.dependencies import DbSession
from app.api.filtering import SearchQuery
from app.api.pagination import Page, Pagination
from app.api.sorting import sort_dependency
from app.core.errors import ErrorResponse
from app.core.pagination import PageParams
from app.models.book import Book
from app.repositories.book import SORTABLE
from app.schemas.book import BookCreate, BookRead, BookUpdate
from app.services.book import BookService

router = APIRouter(prefix="/books", tags=["books"])
_sort = sort_dependency(
    SORTABLE,
    default="title",
    tiebreaker=Book.id,
    nulls_last=True,
)


def get_book_service(session: DbSession) -> BookService:
    return BookService(session)


BookServiceDep = Annotated[BookService, Depends(get_book_service)]
SortOrders = Annotated[list[ColumnElement[Any]], Depends(_sort)]

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "Book not found",
    }
}
_CONFLICT: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "ISBN already exists",
    }
}
_UNPROCESSABLE: dict[int | str, dict[str, Any]] = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": "Invalid payload or referenced entities not found",
    }
}


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a book",
    description=(
        "Create a book with an optional publisher, authors, and categories. "
        "Referenced ids must exist."
    ),
    responses={**_CONFLICT, **_UNPROCESSABLE},
)
def create_book(
    payload: BookCreate,
    service: BookServiceDep,
) -> Book:
    return service.create(payload)


@router.get(
    "",
    response_model=Page[BookRead],
    summary="List books",
    description=(
        "List books with search, filters, sorting, and pagination. "
        "Relations are eager-loaded."
    ),
)
def list_books(
    service: BookServiceDep,
    params: Pagination,
    orders: SortOrders,
    q: SearchQuery = None,
    publisher_id: uuid.UUID | None = None,
    author_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    publication_year_min: Annotated[
        int | None,
        Query(ge=0, le=9999, description="Earliest publication year"),
    ] = None,
    publication_year_max: Annotated[
        int | None,
        Query(ge=0, le=9999, description="Latest publication year"),
    ] = None,
    price_min: Annotated[
        Decimal | None,
        Query(ge=0, description="Minimum price"),
    ] = None,
    price_max: Annotated[
        Decimal | None,
        Query(ge=0, description="Maximum price"),
    ] = None,
) -> Page[BookRead]:
    result = service.list(
        q=q,
        publisher_id=publisher_id,
        author_id=author_id,
        category_id=category_id,
        publication_year_min=publication_year_min,
        publication_year_max=publication_year_max,
        price_min=price_min,
        price_max=price_max,
        order_by=orders,
        page=PageParams(page=params.page, size=params.size),
    )
    return Page[BookRead].create(
        [BookRead.model_validate(book) for book in result.items],
        result.total,
        params,
    )


@router.get(
    "/{book_id}",
    response_model=BookRead,
    summary="Get a book",
    responses=_NOT_FOUND,
)
def get_book(
    book_id: uuid.UUID,
    service: BookServiceDep,
) -> Book:
    return service.get(book_id)


@router.put(
    "/{book_id}",
    response_model=BookRead,
    summary="Replace a book",
    description=(
        "Replace all book fields. Omitted optional fields and relations are cleared."
    ),
    responses={**_NOT_FOUND, **_CONFLICT, **_UNPROCESSABLE},
)
def replace_book(
    book_id: uuid.UUID,
    payload: BookCreate,
    service: BookServiceDep,
) -> Book:
    return service.update(book_id, BookUpdate(**payload.model_dump()))


@router.patch(
    "/{book_id}",
    response_model=BookRead,
    summary="Update a book",
    description=(
        "Update only the provided book fields. Use an empty list to clear "
        "authors or categories."
    ),
    responses={**_NOT_FOUND, **_CONFLICT, **_UNPROCESSABLE},
)
def update_book(
    book_id: uuid.UUID,
    payload: BookUpdate,
    service: BookServiceDep,
) -> Book:
    return service.update(book_id, payload)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    description="Delete a book and its author/category associations.",
    responses=_NOT_FOUND,
)
def delete_book(
    book_id: uuid.UUID,
    service: BookServiceDep,
) -> None:
    service.delete(book_id)
