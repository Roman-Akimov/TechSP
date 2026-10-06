from app.db import SessionLocal
from app import crud


def demo():
    with SessionLocal() as session:
        print("\n=== 1. Список книг ===")
        for book in crud.list_books(session):
            print(book.id, book.title, [g.name for g in book.genres])

        print("\n=== 2. Поиск по жанру ===")
        genres = crud.list_genres(session)
        if genres:
            for book in crud.search_books(session, genre_id=genres[0].id):
                print(book.id, book.title)

        users = crud.list_users(session)
        if not users:
            print("Нет пользователей. Сначала запустите seed.py.")
            return

        reader = users[0]
        books = crud.list_books(session)
        book = books[0]

        print("\n=== 3. Избранное читателя ===")
        for fav in crud.list_favorites(session, reader.id):
            print(fav.book.title)

        print("\n=== 4. Чтение и сохранение прогресса ===")
        progress = crud.save_progress(session, reader.id, book.id, 50)
        print("Последняя страница:", progress.last_page)

        print("\n=== 5. Отзыв ===")
        for review in crud.list_reviews_for_book(session, book.id):
            print(review.rating, review.comment)

        print("\n=== 6. CRUD: изменение книги ===")
        old_title = book.title
        crud.update_book(session, book.id, title=old_title + " — обновлено")
        session.commit()
        refreshed = crud.get_book(session, book.id)
        print("Новое название:", refreshed.title)

        crud.update_book(session, book.id, title=old_title)
        session.commit()

        print("\n=== 7. CRUD: добавление и удаление избранного ===")
        if len(books) > 1:
            other = books[1]
            crud.add_favorite(session, reader.id, other.id)
            session.commit()
            print("Добавлено:", other.title)
            crud.remove_favorite(session, reader.id, other.id)
            session.commit()
            print("Удалено:", other.title)


if __name__ == "__main__":
    demo()
