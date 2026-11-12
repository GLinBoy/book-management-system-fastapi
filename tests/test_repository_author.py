from app.models import Author, Book
from app.repositories.author import AuthorRepository


def test_has_books_is_false_without_books(session):
    author = Author(name="Ursula K. Le Guin")
    session.add(author)
    session.flush()
    repo = AuthorRepository(session)

    assert repo.has_books(author.id) is False


def test_has_books_is_true_when_a_book_references_the_author(session):
    author = Author(name="Ursula K. Le Guin")
    book = Book(title="A Wizard of Earthsea")
    book.authors.append(author)
    session.add(book)
    session.flush()
    repo = AuthorRepository(session)

    assert repo.has_books(author.id) is True
