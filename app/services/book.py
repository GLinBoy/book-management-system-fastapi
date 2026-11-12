import builtins
import uuid
from collections.abc import Collection
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, UnprocessableEntityError
from app.core.pagination import Page, PageParams
from app.models.author import Author
from app.models.book import Book
from app.models.category import Category
from app.models.publisher import Publisher
from app.repositories.author import AuthorRepository
from app.repositories.book import EAGER_OPTIONS, BookRepository
from app.repositories.category import CategoryRepository
from app.repositories.publisher import PublisherRepository
from app.schemas.book import BookCreate, BookUpdate

Details = list[dict[str, Any]]


class BookService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = BookRepository(session)
        self.publishers = PublisherRepository(session)
        self.authors = AuthorRepository(session)
        self.categories = CategoryRepository(session)

    def list(self, *, page: PageParams | None = None) -> Page[Book]:
        return self.repository.list(
            order_by=[Book.title.asc(), Book.id.asc()],
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
