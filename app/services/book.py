import builtins
import uuid
from collections.abc import Collection, Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.errors import NotFoundError, UnprocessableEntityError
from app.core.pagination import Page, PageParams
from app.models.author import Author
from app.models.book import Book
from app.models.category import Category
from app.models.publisher import Publisher
from app.repositories.author import AuthorRepository
from app.repositories.book import EAGER_OPTIONS, SEARCH_COLUMNS, BookRepository
from app.repositories.category import CategoryRepository
from app.repositories.publisher import PublisherRepository
from app.repositories.query import eq_filter, range_filters, search_filter
from app.schemas.book import BookCreate, BookUpdate

Details = list[dict[str, Any]]


class BookService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = BookRepository(session)
        self.publishers = PublisherRepository(session)
        self.authors = AuthorRepository(session)
        self.categories = CategoryRepository(session)

    def list(
        self,
        *,
        q: str | None = None,
        publisher_id: uuid.UUID | None = None,
        author_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        publication_year_min: int | None = None,
        publication_year_max: int | None = None,
        price_min: Decimal | None = None,
        price_max: Decimal | None = None,
        order_by: Sequence[ColumnElement[Any]] = (),
        page: PageParams | None = None,
    ) -> Page[Book]:
        filters: list[ColumnElement[bool]] = []

        search = search_filter(q, SEARCH_COLUMNS)
        if search is not None:
            filters.append(search)

        publisher_filter = eq_filter(Book.publisher_id, publisher_id)
        if publisher_filter is not None:
            filters.append(publisher_filter)

        if author_id is not None:
            filters.append(Book.authors.any(Author.id == author_id))

        if category_id is not None:
            filters.append(Book.categories.any(Category.id == category_id))

        filters.extend(
            range_filters(
                Book.publication_year,
                publication_year_min,
                publication_year_max,
            )
        )
        filters.extend(range_filters(Book.price, price_min, price_max))

        return self.repository.list(
            filters=filters,
            order_by=order_by or [Book.title.asc(), Book.id.asc()],
            page=page,
            options=EAGER_OPTIONS,
        )

    def get(self, book_id: uuid.UUID) -> Book:
        book = self.repository.get_with_relations(book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} not found")
        return book

    def create(self, data: BookCreate) -> Book:
        details: Details = []
        publisher = self._resolve_publisher(data.publisher_id, details)
        authors = self._resolve_authors(data.author_ids, details)
        categories = self._resolve_categories(data.category_ids, details)
        self._raise_for_missing(details)

        values = data.model_dump(exclude={"publisher_id", "author_ids", "category_ids"})
        book = self.repository.create(values)
        book.publisher = publisher
        book.authors = authors
        book.categories = categories
        self.session.flush()
        return self._reload(book)

    def update(self, book_id: uuid.UUID, data: BookUpdate) -> Book:
        book = self.get(book_id)
        changes = data.model_dump(exclude_unset=True)

        author_ids = changes.pop("author_ids", None)
        category_ids = changes.pop("category_ids", None)
        publisher_provided = "publisher_id" in changes

        details: Details = []
        publisher = None
        if publisher_provided:
            publisher = self._resolve_publisher(changes.pop("publisher_id"), details)
        authors = (
            self._resolve_authors(author_ids, details)
            if author_ids is not None
            else None
        )
        categories = (
            self._resolve_categories(category_ids, details)
            if category_ids is not None
            else None
        )
        self._raise_for_missing(details)

        if publisher_provided:
            book.publisher = publisher
        if authors is not None:
            book.authors = authors
        if categories is not None:
            book.categories = categories

        if changes:
            self.repository.update(book, changes)
        else:
            self.session.flush()
        return self._reload(book)

    def delete(self, book_id: uuid.UUID) -> None:
        book = self.get(book_id)
        self.repository.delete(book)

    def set_authors(
        self,
        book_id: uuid.UUID,
        author_ids: Collection[uuid.UUID],
    ) -> Book:
        book = self.get(book_id)
        details: Details = []
        authors = self._resolve_authors(author_ids, details)
        self._raise_for_missing(details)
        book.authors = authors
        self.session.flush()
        return self._reload(book)

    def set_categories(
        self,
        book_id: uuid.UUID,
        category_ids: Collection[uuid.UUID],
    ) -> Book:
        book = self.get(book_id)
        details: Details = []
        categories = self._resolve_categories(category_ids, details)
        self._raise_for_missing(details)
        book.categories = categories
        self.session.flush()
        return self._reload(book)

    def _reload(self, book: Book) -> Book:
        return self.repository.get_with_relations(book.id) or book

    def _resolve_publisher(
        self,
        publisher_id: uuid.UUID | None,
        details: Details,
    ) -> Publisher | None:
        if publisher_id is None:
            return None
        publisher = self.publishers.get(publisher_id)
        if publisher is None:
            details.append(
                {
                    "loc": ["body", "publisher_id"],
                    "msg": f"Publisher {publisher_id} not found",
                    "type": "value_error",
                }
            )
        return publisher

    def _resolve_authors(
        self,
        author_ids: Collection[uuid.UUID],
        details: Details,
    ) -> builtins.list[Author]:
        ids = list(dict.fromkeys(author_ids))
        if not ids:
            return []
        authors = {author.id: author for author in self.authors.get_many(ids)}
        missing = [author_id for author_id in ids if author_id not in authors]
        if missing:
            details.append(
                {
                    "loc": ["body", "author_ids"],
                    "msg": "Authors not found: "
                    + ", ".join(str(author_id) for author_id in missing),
                    "type": "value_error",
                }
            )
        return [authors[author_id] for author_id in ids if author_id in authors]

    def _resolve_categories(
        self,
        category_ids: Collection[uuid.UUID],
        details: Details,
    ) -> builtins.list[Category]:
        ids = list(dict.fromkeys(category_ids))
        if not ids:
            return []
        categories = {
            category.id: category for category in self.categories.get_many(ids)
        }
        missing = [category_id for category_id in ids if category_id not in categories]
        if missing:
            details.append(
                {
                    "loc": ["body", "category_ids"],
                    "msg": "Categories not found: "
                    + ", ".join(str(category_id) for category_id in missing),
                    "type": "value_error",
                }
            )
        return [
            categories[category_id] for category_id in ids if category_id in categories
        ]

    def _raise_for_missing(self, details: Details) -> None:
        if details:
            raise UnprocessableEntityError(
                "Referenced entities not found",
                details=details,
            )
