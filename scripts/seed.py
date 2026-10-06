from app.db import SessionLocal
from app import crud
from app.models import Book


def seed():
    with SessionLocal() as session:
        if session.query(Book).first():
            print("БД уже содержит книги. Seed пропущен.")
            return

        reader_role = crud.create_role(
            session, "reader", "Читатель", "Конечный пользователь библиотеки"
        )
        admin_role = crud.create_role(
            session, "admin", "Администратор", "Управление каталогом"
        )

        reader = crud.create_user(
            session,
            "reader@example.com",
            "demo_hash_reader",
            "Иван Петров",
            reader_role.id,
        )
        admin = crud.create_user(
            session,
            "admin@example.com",
            "demo_hash_admin",
            "Администратор",
            admin_role.id,
        )

        fiction = crud.create_genre(session, "Фантастика", "Фантастические произведения")
        classic = crud.create_genre(session, "Классика", "Классическая литература")
        science = crud.create_genre(session, "Научно-популярная", "Научно-популярные книги")

        book1 = crud.create_book(
            session,
            title="Марсианские хроники",
            isbn="9780000000001",
            description="Тестовая книга для демонстрации ЛР №1.",
            publication_year=1950,
            publisher="Test Publisher",
            cover_url="https://example.com/cover1.jpg",
            file_url="/books/martian.pdf",
            total_pages=250,
            language="ru",
            genres=[fiction],
        )
        book2 = crud.create_book(
            session,
            title="История науки",
            isbn="9780000000002",
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
        crud.create_review(session, reader.id, book1.id, 5, "Интересная книга.")

        session.commit()

        print(f"Создан читатель: {reader.id}")
        print(f"Создан администратор: {admin.id}")
        print(f"Созданы книги: {book1.id}, {book2.id}")


if __name__ == "__main__":
    seed()
