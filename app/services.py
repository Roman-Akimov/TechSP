from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import crud
from app.models import Book, Genre, Role, User, Review
from app.schemas import (
    UserRegisterIn,
    UserLoginIn,
    BookCreateIn,
    BookUpdateIn,
    GenreCreateIn,
    ProgressUpdateIn,
    ReviewCreateIn,
)
from app.security import hash_password, verify_password, create_access_token

class LibraryService:
    def __init__(self, session: Session):
        self.session = session

    # аутентификация и пользователи
    def register_user(self, data: UserRegisterIn) -> User:
        existing = crud.get_user_by_email(self.session, data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует",
            )

        role = self.session.scalar(select(Role).where(Role.code == data.role_code))
        if not role:
            role_name = "Администратор" if data.role_code == "admin" else "Читатель"
            role = crud.create_role(self.session, code=data.role_code, name=role_name)

        user = crud.create_user(
            self.session,
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role_id=role.id,
        )
        self.session.commit()
        return crud.get_user(self.session, user.id)

    def authenticate_user(self, data: UserLoginIn) -> str:
        user = crud.get_user_by_email(self.session, data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Учетная запись заблокирована",
            )
        return create_access_token(
            user_id=user.id,
            role_code=user.role.code,
            login=user.email,
        )

    # жанры
    def list_genres(self) -> list[Genre]:
        return crud.list_genres(self.session)

    def get_genre_or_404(self, genre_id: int) -> Genre:
        genre = crud.get_genre(self.session, genre_id)
        if not genre:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Жанр не найден")
        return genre

    def create_genre(self, data: GenreCreateIn) -> Genre:
        existing = self.session.scalar(select(Genre).where(Genre.name == data.name))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Жанр с таким названием уже существует",
            )
        genre = crud.create_genre(self.session, name=data.name, description=data.description)
        self.session.commit()
        self.session.refresh(genre)
        return genre

    def update_genre(self, genre_id: int, data: GenreCreateIn) -> Genre:
        self.get_genre_or_404(genre_id)
        duplicate = self.session.scalar(
            select(Genre).where(Genre.name == data.name, Genre.id != genre_id)
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Другой жанр с таким названием уже существует",
            )
        genre = crud.update_genre(
            self.session, genre_id, name=data.name, description=data.description
        )
        self.session.commit()
        self.session.refresh(genre)
        return genre

    def delete_genre(self, genre_id: int) -> None:
        deleted = crud.delete_genre(self.session, genre_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Жанр не найден")
        self.session.commit()

    # Книги
    def list_books(
        self,
        genre_name: str | None = None,
        language: str | None = None,
        publication_year: int | None = None,
        title_part: str | None = None,
    ) -> list[Book]:
        stmt = select(Book).options(selectinload(Book.genres)).order_by(Book.id)
        if genre_name:
            stmt = stmt.where(Book.genres.any(Genre.name == genre_name))
        if language:
            stmt = stmt.where(Book.language == language)
        if publication_year is not None:
            stmt = stmt.where(Book.publication_year == publication_year)
        if title_part:
            stmt = stmt.where(Book.title.ilike(f"%{title_part}%"))
        return list(self.session.scalars(stmt).all())

    def get_book_or_404(self, book_id: int) -> Book:
        book = crud.get_book(self.session, book_id)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книга не найдена")
        return book

    def create_book(self, data: BookCreateIn) -> Book:
        if data.isbn:
            existing_isbn = self.session.scalar(select(Book).where(Book.isbn == data.isbn))
            if existing_isbn:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Книга с таким ISBN уже существует",
                )

        genres = []
        if data.genre_ids:
            genres = list(
                self.session.scalars(select(Genre).where(Genre.id.in_(data.genre_ids))).all()
            )

        book = crud.create_book(
            self.session,
            title=data.title,
            file_url=data.file_url,
            isbn=data.isbn,
            description=data.description,
            publication_year=data.publication_year,
            publisher=data.publisher,
            cover_url=data.cover_url,
            total_pages=data.total_pages,
            language=data.language,
            genres=genres,
        )
        self.session.commit()
        return self.get_book_or_404(book.id)

    def update_book(self, book_id: int, data: BookUpdateIn) -> Book:
        book = self.get_book_or_404(book_id)
        update_data = data.model_dump(exclude_unset=True)

        if "isbn" in update_data and update_data["isbn"]:
            dup = self.session.scalar(
                select(Book).where(Book.isbn == update_data["isbn"], Book.id != book_id)
            )
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Другая книга с таким ISBN уже существует",
                )

        genre_ids = update_data.pop("genre_ids", None)
        non_nullable_fields = {"title", "file_url", "total_pages", "language"}

        for field, value in update_data.items():
            if field in non_nullable_fields and value is None:
                continue
            setattr(book, field, value)

        if genre_ids is not None:
            genres = list(
                self.session.scalars(select(Genre).where(Genre.id.in_(genre_ids))).all()
            )
            book.genres = genres

        self.session.flush()
        self.session.commit()
        return self.get_book_or_404(book.id)

    def delete_book(self, book_id: int) -> None:
        deleted = crud.delete_book(self.session, book_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Книга не найдена")
        self.session.commit()

    # операции читателя (избранное, прогресс, отзывы)
    def add_to_favorites(self, user_id: int, book_id: int) -> None:
        self.get_book_or_404(book_id)
        crud.add_favorite(self.session, user_id=user_id, book_id=book_id)
        self.session.commit()

    def remove_from_favorites(self, user_id: int, book_id: int) -> None:
        removed = crud.remove_favorite(self.session, user_id=user_id, book_id=book_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Книга не найдена в избранном"
            )
        self.session.commit()

    def get_user_favorites(self, user_id: int) -> list[Book]:
        return crud.list_user_favorites(self.session, user_id=user_id)

    def get_reading_progress(self, user_id: int, book_id: int):
        self.get_book_or_404(book_id)
        progress = crud.get_progress(self.session, user_id=user_id, book_id=book_id)
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Прогресс чтения по данной книге еще не сохранен",
            )
        return progress

    def save_reading_progress(self, user_id: int, book_id: int, data: ProgressUpdateIn):
        book = self.get_book_or_404(book_id)
        if book.total_pages and data.last_page > book.total_pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Страница ({data.last_page}) превышает объем книги ({book.total_pages})",
            )
        progress = crud.save_progress(
            self.session,
            user_id=user_id,
            book_id=book_id,
            last_page=data.last_page,
        )
        self.session.commit()
        return progress

    def add_or_update_review(self, user_id: int, book_id: int, data: ReviewCreateIn) -> Review:
        self.get_book_or_404(book_id)
        review = crud.upsert_review(
            self.session,
            user_id=user_id,
            book_id=book_id,
            rating=data.rating,
            comment=data.comment,
        )
        self.session.commit()
        self.session.refresh(review)
        return review

    def list_book_reviews(self, book_id: int) -> list[Review]:
        self.get_book_or_404(book_id)
        return crud.list_reviews_for_book(self.session, book_id=book_id)

    def delete_user_review(self, user_id: int, book_id: int) -> None:
        review = self.session.scalar(
            select(Review).where(Review.user_id == user_id, Review.book_id == book_id)
        )
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ваш отзыв на эту книгу не найден",
            )
        crud.delete_review(self.session, review.id)
        self.session.commit()