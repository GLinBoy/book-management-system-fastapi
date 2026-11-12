from app.models import Book, Category
from app.repositories.category import CategoryRepository


def test_has_books_is_false_without_books(session):
    category = Category(name="Science Fiction")
    session.add(category)
    session.flush()
    repo = CategoryRepository(session)

    assert repo.has_books(category.id) is False


def test_has_books_is_true_when_a_book_references_the_category(session):
    category = Category(name="Science Fiction")
    book = Book(title="Dune")
    book.categories.append(category)
    session.add(book)
    session.flush()
    repo = CategoryRepository(session)

    assert repo.has_books(category.id) is True
