from sqlalchemy import select

from app.db import SessionLocal
from app import crud
from app.models import Book, Genre, Role, User
from app.security import hash_password


def get_or_create_role(session, code, name, description):
    role = session.scalar(
        select(Role).where(Role.code == code)
    )
    if role is None:
        role = crud.create_role(session, code, name, description)
    return role


def get_or_create_user(session, email, password, name, role):
    user = crud.get_user_by_email(session, email)
    if user is None:
        user = crud.create_user(
            session,
            email,
            hash_password(password),
            name,
            role.id,
        )
    return user


def get_or_create_genre(session, name, description):
    genre = session.scalar(
        select(Genre).where(Genre.name == name)
    )
    if genre is None:
        genre = crud.create_genre(session, name, description)
    return genre


def get_or_create_book(session, isbn, **data):
    book = session.scalar(
        select(Book).where(Book.isbn == isbn)
    )
    if book is None:
        book = crud.create_book(session, isbn=isbn, **data)
    return book


def seed():
    with SessionLocal() as session:
        reader_role = get_or_create_role(
            session, "reader", "Читатель",
            "Конечный пользователь библиотеки"
        )

        admin_role = get_or_create_role(
            session, "admin", "Администратор",
            "Управление каталогом"
        )

        reader = get_or_create_user(
            session,
            "reader@example.com",
            "password123",
            "Иван Петров",
            reader_role,
        )

        admin = get_or_create_user(
            session,
            "admin@example.com",
            "password123",
            "Администратор",
            admin_role,
        )

        fiction = get_or_create_genre(
            session, "Фантастика",
            "Фантастические произведения"
        )

        classic = get_or_create_genre(
            session, "Классика",
            "Классическая литература"
        )

        science = get_or_create_genre(
            session, "Научно-популярная",
            "Научно-популярные книги"
        )

        book1 = get_or_create_book(
            session,
            "9780000000001",
            title="Марсианские хроники",
            description="Тестовая книга для демонстрации.",
            publication_year=1950,
            publisher="Test Publisher",
            cover_url="https://example.com/cover1.jpg",
            file_url="/books/martian.pdf",
            total_pages=250,
            language="ru",
            genres=[fiction],
        )

        book2 = get_or_create_book(
            session,
            "9780000000002",
            title="История науки",
            description="Тестовая научно-популярная книга.",
            publication_year=2020,
            publisher="Test Publisher",
            cover_url=None,
            file_url="/books/science.pdf",
            total_pages=320,
            language="ru",
            genres=[science, classic],
        )

        crud.add_favorite(session, reader.id, book1.id)
        crud.save_progress(session, reader.id, book1.id, 37)

        crud.upsert_review(
            session, reader.id, book1.id, 5,
            "Интересная книга."
        )

        session.commit()

        print("========== SEED COMPLETED ==========")
        print(f"Reader: {reader.email}, ID: {reader.id}")
        print(f"Admin: {admin.email}, ID: {admin.id}")
        print(f"Books: {book1.title}, {book2.title}")
        print("Genres, favorites, progress and reviews ready.")
        print("====================================")


if __name__ == "__main__":
    seed()
