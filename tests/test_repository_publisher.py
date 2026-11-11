from app.models import Book, Publisher
from app.repositories.publisher import PublisherRepository


def test_has_books_is_false_without_books(session):
    publisher = Publisher(name="Ace")
    session.add(publisher)
    session.flush()
    repo = PublisherRepository(session)

    assert repo.has_books(publisher.id) is False


def test_has_books_is_true_when_a_book_references_the_publisher(session):
    publisher = Publisher(name="Ace")
    session.add(publisher)
    session.flush()
    session.add(Book(title="Dune", publisher_id=publisher.id))
    session.flush()
    repo = PublisherRepository(session)

    assert repo.has_books(publisher.id) is True
