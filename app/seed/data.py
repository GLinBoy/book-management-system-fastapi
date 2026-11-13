"""Deterministic development data generation with Faker."""

import random
from dataclasses import dataclass

from faker import Faker

from app.models import Author, Book, Category, Publisher

DEFAULT_SEED = 42

PUBLISHER_COUNT = 20
AUTHOR_COUNT = 50
BOOK_COUNT = 300

MIN_BOOK_AUTHORS = 1
MAX_BOOK_AUTHORS = 3
MIN_BOOK_CATEGORIES = 1
MAX_BOOK_CATEGORIES = 3

# Fraction of books without a publisher, to exercise the nullable relation.
PUBLISHERLESS_BOOK_RATIO = 0.1

MIN_ESTABLISHED_YEAR = 1800
MAX_ESTABLISHED_YEAR = 2020
MIN_BIRTH_YEAR = 1920
MAX_BIRTH_YEAR = 1990
MIN_PUBLICATION_YEAR = 1950
MAX_PUBLICATION_YEAR = 2025

MIN_BOOK_PRICE = 5
MAX_BOOK_PRICE = 200

CATEGORY_NAMES = (
    "Science Fiction",
    "Fantasy",
    "Mystery",
    "Thriller",
    "Romance",
    "Historical Fiction",
    "Horror",
    "Non-Fiction",
    "Biography",
    "Science",
    "Technology",
    "Philosophy",
    "Poetry",
    "Young Adult",
    "Business",
)


@dataclass(frozen=True)
class SeedData:
    """In-memory entities ready to be added to a session."""

    publishers: list[Publisher]
    authors: list[Author]
    categories: list[Category]
    books: list[Book]


def generate_seed_data(seed: int = DEFAULT_SEED) -> SeedData:
    """Build the development data set without touching the database.

    The same seed always produces the same values and relationships. Entity
    primary keys are assigned when rows are flushed, so they are not part of
    the deterministic output.
    """
    faker = Faker()
    faker.seed_instance(seed)
    rng = random.Random(seed)

    publishers = [_build_publisher(faker, rng) for _ in range(PUBLISHER_COUNT)]
    authors = [_build_author(faker, rng) for _ in range(AUTHOR_COUNT)]
    categories = [_build_category(faker, name) for name in CATEGORY_NAMES]
    seen_isbns: set[str] = set()
    books = [
        _build_book(faker, rng, publishers, authors, categories, seen_isbns)
        for _ in range(BOOK_COUNT)
    ]
    return SeedData(
        publishers=publishers,
        authors=authors,
        categories=categories,
        books=books,
    )


def _build_publisher(faker: Faker, rng: random.Random) -> Publisher:
    return Publisher(
        name=faker.company(),
        country=faker.country(),
        established_year=rng.randint(MIN_ESTABLISHED_YEAR, MAX_ESTABLISHED_YEAR),
    )


def _build_author(faker: Faker, rng: random.Random) -> Author:
    return Author(
        name=faker.name(),
        biography=faker.paragraph(nb_sentences=3),
        birth_year=rng.randint(MIN_BIRTH_YEAR, MAX_BIRTH_YEAR),
    )


def _build_category(faker: Faker, name: str) -> Category:
    return Category(name=name, description=faker.sentence())


def _build_book(
    faker: Faker,
    rng: random.Random,
    publishers: list[Publisher],
    authors: list[Author],
    categories: list[Category],
    seen_isbns: set[str],
) -> Book:
    publisher = (
        None if rng.random() < PUBLISHERLESS_BOOK_RATIO else rng.choice(publishers)
    )
    return Book(
        title=faker.sentence(nb_words=3).rstrip("."),
        isbn=_unique_isbn(faker, seen_isbns),
        publication_year=rng.randint(MIN_PUBLICATION_YEAR, MAX_PUBLICATION_YEAR),
        price=faker.pydecimal(
            left_digits=3,
            right_digits=2,
            min_value=MIN_BOOK_PRICE,
            max_value=MAX_BOOK_PRICE,
        ),
        description=faker.paragraph(nb_sentences=3),
        publisher=publisher,
        authors=rng.sample(
            authors,
            rng.randint(MIN_BOOK_AUTHORS, MAX_BOOK_AUTHORS),
        ),
        categories=rng.sample(
            categories,
            rng.randint(MIN_BOOK_CATEGORIES, MAX_BOOK_CATEGORIES),
        ),
    )


def _unique_isbn(faker: Faker, seen: set[str]) -> str:
    while True:
        isbn = faker.isbn13(separator="")
        if isbn not in seen:
            seen.add(isbn)
            return isbn
