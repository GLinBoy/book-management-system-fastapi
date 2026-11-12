import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.sql.elements import ColumnElement

from app.api.dependencies import DbSession
from app.api.filtering import SearchQuery
from app.api.pagination import Page, Pagination
from app.api.sorting import sort_dependency
from app.core.errors import ErrorResponse
from app.core.pagination import PageParams
from app.models.author import Author
from app.repositories.author import SORTABLE
from app.schemas.author import AuthorCreate, AuthorRead, AuthorUpdate
from app.schemas.book import BookSummary
from app.services.author import AuthorService

router = APIRouter(prefix="/authors", tags=["authors"])

_sort = sort_dependency(SORTABLE, default="name", tiebreaker=Author.id)


def get_author_service(session: DbSession) -> AuthorService:
    return AuthorService(session)


AuthorServiceDep = Annotated[AuthorService, Depends(get_author_service)]
SortOrders = Annotated[list[ColumnElement[Any]], Depends(_sort)]


@router.post(
    "",
    response_model=AuthorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an author",
    description="Create an author with an optional biography and birth year.",
)
def create_author(
    payload: AuthorCreate,
    service: AuthorServiceDep,
) -> Author:
    return service.create(payload)


@router.get(
    "",
    response_model=Page[AuthorRead],
    summary="List authors",
    description=(
        "List authors with optional name/biography search, birth-year range, "
        "sorting, and pagination."
    ),
)
def list_authors(
    service: AuthorServiceDep,
    params: Pagination,
    orders: SortOrders,
    q: SearchQuery = None,
    birth_year_min: Annotated[
        int | None,
        Query(ge=0, le=9999, description="Earliest birth year"),
    ] = None,
    birth_year_max: Annotated[
        int | None,
        Query(ge=0, le=9999, description="Latest birth year"),
    ] = None,
) -> Page[AuthorRead]:
    result = service.list(
        q=q,
        birth_year_min=birth_year_min,
        birth_year_max=birth_year_max,
        order_by=orders,
        page=PageParams(page=params.page, size=params.size),
    )
    return Page[AuthorRead].create(
        [AuthorRead.model_validate(author) for author in result.items],
        result.total,
        params,
    )


@router.get(
    "/{author_id}",
    response_model=AuthorRead,
    summary="Get an author",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Author not found",
        }
    },
)
def get_author(
    author_id: uuid.UUID,
    service: AuthorServiceDep,
) -> Author:
    return service.get(author_id)


@router.put(
    "/{author_id}",
    response_model=AuthorRead,
    summary="Replace an author",
    description="Replace all author fields. Omitted optional fields are cleared.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Author not found",
        }
    },
)
def replace_author(
    author_id: uuid.UUID,
    payload: AuthorCreate,
    service: AuthorServiceDep,
) -> Author:
    return service.update(author_id, AuthorUpdate(**payload.model_dump()))


@router.patch(
    "/{author_id}",
    response_model=AuthorRead,
    summary="Update an author",
    description="Update only the provided author fields.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Author not found",
        }
    },
)
def update_author(
    author_id: uuid.UUID,
    payload: AuthorUpdate,
    service: AuthorServiceDep,
) -> Author:
    return service.update(author_id, payload)


@router.delete(
    "/{author_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an author",
    description="Delete an author that has no books.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Author not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Author still has books",
        },
    },
)
def delete_author(
    author_id: uuid.UUID,
    service: AuthorServiceDep,
) -> None:
    service.delete(author_id)


@router.get(
    "/{author_id}/books",
    response_model=Page[BookSummary],
    summary="List books by author",
    description="List the books associated with an author, with pagination.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Author not found",
        }
    },
)
def list_author_books(
    author_id: uuid.UUID,
    service: AuthorServiceDep,
    params: Pagination,
) -> Page[BookSummary]:
    result = service.list_books(
        author_id,
        page=PageParams(page=params.page, size=params.size),
    )
    return Page[BookSummary].create(
        [BookSummary.model_validate(book) for book in result.items],
        result.total,
        params,
    )
