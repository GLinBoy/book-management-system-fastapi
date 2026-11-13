import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models import Author, Book
from app.seed import generate_seed_data, seed_database
from app.seed.cli import main


@pytest.fixture
def cli_engine(engine, monkeypatch):
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr("app.seed.cli.get_session_factory", lambda: factory)
    return engine


def _count(engine, model) -> int:
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(model)) or 0


def test_main_seeds_an_empty_database(cli_engine, capsys):
    assert main([]) == 0

    output = capsys.readouterr().out
    assert "Seeded 20 publishers, 50 authors, 15 categories, 300 books." in output
    assert _count(cli_engine, Book) == 300


def test_main_skips_when_data_exists(cli_engine, capsys):
    main([])
    capsys.readouterr()

    assert main([]) == 0

    output = capsys.readouterr().out
    assert "Seed skipped" in output
    assert "--reset" in output
    assert _count(cli_engine, Book) == 300


def test_main_reset_replaces_existing_data(cli_engine, capsys):
    with Session(cli_engine) as session:
        seed_database(session)
        session.add(Author(name="Extra Author"))
        session.commit()
    capsys.readouterr()

    assert main(["--reset"]) == 0

    assert "Seeded" in capsys.readouterr().out
    assert _count(cli_engine, Author) == 50
    assert _count(cli_engine, Book) == 300


def test_main_uses_requested_seed(cli_engine, capsys):
    assert main(["--seed", "7"]) == 0
    capsys.readouterr()

    with Session(cli_engine) as session:
        titles = sorted(session.scalars(select(Book.title)).all())
    expected = sorted(book.title for book in generate_seed_data(seed=7).books)
    assert titles == expected


def test_help_exits_successfully(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0
    assert "usage:" in capsys.readouterr().out
