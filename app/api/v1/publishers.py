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
from app.models.publisher import Publisher
from app.repositories.publisher import SORTABLE
from app.schemas.publisher import PublisherCreate, PublisherRead, PublisherUpdate
from app.services.publisher import PublisherService

router = APIRouter(prefix="/publishers", tags=["publishers"])

_sort = sort_dependency(SORTABLE, default="name", tiebreaker=Publisher.id)


def get_publisher_service(session: DbSession) -> PublisherService:
    return PublisherService(session)


PublisherServiceDep = Annotated[PublisherService, Depends(get_publisher_service)]
SortOrders = Annotated[list[ColumnElement[Any]], Depends(_sort)]


@router.post(
    "",
    response_model=PublisherRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a publisher",
    description="Create a publisher with an optional country and established year.",
)
def create_publisher(
    payload: PublisherCreate,
    service: PublisherServiceDep,
) -> Publisher:
    return service.create(payload)


@router.get(
    "",
    response_model=Page[PublisherRead],
    summary="List publishers",
    description=(
        "List publishers with optional name search, country filter, "
        "established-year range, sorting, and pagination."
    ),
)
def list_publishers(
    service: PublisherServiceDep,
    params: Pagination,
    orders: SortOrders,
    q: SearchQuery = None,
    country: Annotated[
        str | None,
        Query(max_length=100, description="Exact country match"),
    ] = None,
    established_year_min: Annotated[
        int | None,
        Query(ge=0, le=9999, description="Earliest established year"),
    ] = None,
    established_year_max: Annotated[
        int | None,
        Query(ge=0, le=9999, description="Latest established year"),
    ] = None,
) -> Page[PublisherRead]:
    result = service.list(
        q=q,
        country=country,
        established_year_min=established_year_min,
        established_year_max=established_year_max,
        order_by=orders,
        page=PageParams(page=params.page, size=params.size),
    )
    return Page[PublisherRead].create(
        [PublisherRead.model_validate(publisher) for publisher in result.items],
        result.total,
        params,
    )


@router.get(
    "/{publisher_id}",
    response_model=PublisherRead,
    summary="Get a publisher",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Publisher not found",
        }
    },
)
def get_publisher(
    publisher_id: uuid.UUID,
    service: PublisherServiceDep,
) -> Publisher:
    return service.get(publisher_id)


@router.put(
    "/{publisher_id}",
    response_model=PublisherRead,
    summary="Replace a publisher",
    description="Replace all publisher fields. Omitted optional fields are cleared.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Publisher not found",
        }
    },
)
def replace_publisher(
    publisher_id: uuid.UUID,
    payload: PublisherCreate,
    service: PublisherServiceDep,
) -> Publisher:
    return service.update(publisher_id, PublisherUpdate(**payload.model_dump()))


@router.patch(
    "/{publisher_id}",
    response_model=PublisherRead,
    summary="Update a publisher",
    description="Update only the provided publisher fields.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Publisher not found",
        }
    },
)
def update_publisher(
    publisher_id: uuid.UUID,
    payload: PublisherUpdate,
    service: PublisherServiceDep,
) -> Publisher:
    return service.update(publisher_id, payload)


@router.delete(
    "/{publisher_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a publisher",
    description="Delete a publisher that has no books.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Publisher not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Publisher still has books",
        },
    },
)
def delete_publisher(
    publisher_id: uuid.UUID,
    service: PublisherServiceDep,
) -> None:
    service.delete(publisher_id)
