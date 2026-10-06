import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app import crud
from app.db import Base


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://library:library@localhost:5432/library_db",
)


@pytest.fixture()
def session():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL недоступен: {exc}")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as s:
        # Тестовая схема очищается перед каждым тестом.
        for table in reversed(Base.metadata.sorted_tables):
            s.execute(table.delete())
        s.commit()
        yield s
    engine.dispose()


def make_basic_data(session):
    role = crud.create_role(session, "reader", "Читатель")
    user = crud.create_user(session, "test@example.com", "hash", "Тестовый пользователь", role.id)
    genre = crud.create_genre(session, "Фантастика")
    book = crud.create_book(
        session,
        title="Тестовая книга",
        isbn="9999999999999",
        file_url="/test.pdf",
        total_pages=100,
        publication_year=2024,
        genres=[genre],
    )
    session.commit()
    return user, genre, book


def test_user_crud(session):
    user, _, _ = make_basic_data(session)
    assert crud.get_user(session, user.id).email == "test@example.com"

    crud.update_user(session, user.id, full_name="Новое имя")
    session.commit()
    assert crud.get_user(session, user.id).full_name == "Новое имя"

    assert crud.delete_user(session, user.id) is True
    session.commit()
    assert crud.get_user(session, user.id) is None


def test_book_search_and_genre_m2m(session):
    _, genre, book = make_basic_data(session)
    result = crud.search_books(session, genre_id=genre.id)
    assert [b.id for b in result] == [book.id]


def test_favorite_and_progress(session):
    user, _, book = make_basic_data(session)

    crud.add_favorite(session, user.id, book.id)
    progress = crud.save_progress(session, user.id, book.id, 42)
    session.commit()

    assert len(crud.list_favorites(session, user.id)) == 1
    assert crud.get_progress(session, user.id, book.id).last_page == 42

    crud.save_progress(session, user.id, book.id, 77)
    session.commit()
    assert crud.get_progress(session, user.id, book.id).last_page == 77

    assert crud.remove_favorite(session, user.id, book.id) is True
    session.commit()
    assert crud.list_favorites(session, user.id) == []


def test_review_crud(session):
    user, _, book = make_basic_data(session)
    review = crud.create_review(session, user.id, book.id, 5, "Отлично")
    session.commit()

    assert crud.list_reviews_for_book(session, book.id)[0].rating == 5

    crud.update_review(session, review.id, rating=4)
    session.commit()
    assert crud.list_reviews_for_book(session, book.id)[0].rating == 4

    assert crud.delete_review(session, review.id) is True
    session.commit()
    assert crud.list_reviews_for_book(session, book.id) == []
