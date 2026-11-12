import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.sql.elements import ColumnElement

from app.api.dependencies import DbSession
from app.api.filtering import SearchQuery
from app.api.pagination import Page, Pagination
from app.api.sorting import sort_dependency
from app.core.errors import ErrorResponse
from app.core.pagination import PageParams
from app.models.category import Category
from app.repositories.category import SORTABLE
from app.schemas.book import BookSummary
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])

_sort = sort_dependency(SORTABLE, default="name", tiebreaker=Category.id)


def get_category_service(session: DbSession) -> CategoryService:
    return CategoryService(session)


CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
SortOrders = Annotated[list[ColumnElement[Any]], Depends(_sort)]


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
    description="Create a category with a unique name and an optional description.",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Category name already exists",
        }
    },
)
def create_category(
    payload: CategoryCreate,
    service: CategoryServiceDep,
) -> Category:
    return service.create(payload)


@router.get(
    "",
    response_model=Page[CategoryRead],
    summary="List categories",
    description=(
        "List categories with optional name/description search, sorting, "
        "and pagination."
    ),
)
def list_categories(
    service: CategoryServiceDep,
    params: Pagination,
    orders: SortOrders,
    q: SearchQuery = None,
) -> Page[CategoryRead]:
    result = service.list(
        q=q,
        order_by=orders,
        page=PageParams(page=params.page, size=params.size),
    )
    return Page[CategoryRead].create(
        [CategoryRead.model_validate(category) for category in result.items],
        result.total,
        params,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Get a category",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Category not found",
        }
    },
)
def get_category(
    category_id: uuid.UUID,
    service: CategoryServiceDep,
) -> Category:
    return service.get(category_id)


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Replace a category",
    description="Replace all category fields. Omitted optional fields are cleared.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Category not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Category name already exists",
        },
    },
)
def replace_category(
    category_id: uuid.UUID,
    payload: CategoryCreate,
    service: CategoryServiceDep,
) -> Category:
    return service.update(category_id, CategoryUpdate(**payload.model_dump()))


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Update a category",
    description="Update only the provided category fields.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Category not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Category name already exists",
        },
    },
)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    service: CategoryServiceDep,
) -> Category:
    return service.update(category_id, payload)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
    description="Delete a category that has no books.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Category not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Category still has books",
        },
    },
)
def delete_category(
    category_id: uuid.UUID,
    service: CategoryServiceDep,
) -> None:
    service.delete(category_id)


@router.get(
    "/{category_id}/books",
    response_model=Page[BookSummary],
    summary="List books by category",
    description="List the books associated with a category, with pagination.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Category not found",
        }
    },
)
def list_category_books(
    category_id: uuid.UUID,
    service: CategoryServiceDep,
    params: Pagination,
) -> Page[BookSummary]:
    result = service.list_books(
        category_id,
        page=PageParams(page=params.page, size=params.size),
    )
    return Page[BookSummary].create(
        [BookSummary.model_validate(book) for book in result.items],
        result.total,
        params,
    )
