from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models import Book, Favorite, Genre, ReadingProgress, Review, Role, User


# ---------- Роли ----------

def create_role(session: Session, code: str, name: str, description: str | None = None) -> Role:
    obj = Role(code=code, name=name, description=description)
    session.add(obj)
    session.flush()
    return obj


def get_role(session: Session, role_id: int) -> Role | None:
    return session.get(Role, role_id)


def list_roles(session: Session) -> list[Role]:
    return list(session.scalars(select(Role).order_by(Role.id)))


# ---------- Пользователи ----------

def create_user(
    session: Session,
    email: str,
    password_hash: str,
    full_name: str,
    role_id: int,
) -> User:
    obj = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role_id=role_id,
    )
    session.add(obj)
    session.flush()
    return obj


def get_user(session: Session, user_id: int) -> User | None:
    return session.scalar(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )


def list_users(session: Session) -> list[User]:
    return list(
        session.scalars(
            select(User).options(selectinload(User.role)).order_by(User.id)
        )
    )


def update_user(session: Session, user_id: int, **changes) -> User | None:
    obj = session.get(User, user_id)
    if obj is None:
        return None
    for key, value in changes.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    session.flush()
    return obj


def delete_user(session: Session, user_id: int) -> bool:
    obj = session.get(User, user_id)
    if obj is None:
        return False
    session.delete(obj)
    session.flush()
    return True


# ---------- Жанры ----------

def create_genre(session: Session, name: str, description: str | None = None) -> Genre:
    obj = Genre(name=name, description=description)
    session.add(obj)
    session.flush()
    return obj


def get_genre(session: Session, genre_id: int) -> Genre | None:
    return session.get(Genre, genre_id)


def list_genres(session: Session) -> list[Genre]:
    return list(session.scalars(select(Genre).order_by(Genre.name)))


def update_genre(session: Session, genre_id: int, **changes) -> Genre | None:
    obj = session.get(Genre, genre_id)
    if obj is None:
        return None
    for key, value in changes.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    session.flush()
    return obj


def delete_genre(session: Session, genre_id: int) -> bool:
    obj = session.get(Genre, genre_id)
    if obj is None:
        return False
    session.delete(obj)
    session.flush()
    return True


# ---------- Books ----------

def create_book(session: Session, **data) -> Book:
    genres = data.pop("genres", [])
    obj = Book(**data)
    obj.genres = genres
    session.add(obj)
    session.flush()
    return obj


def get_book(session: Session, book_id: int) -> Book | None:
    return session.scalar(
        select(Book)
        .options(selectinload(Book.genres))
        .where(Book.id == book_id)
    )


def list_books(session: Session) -> list[Book]:
    return list(
        session.scalars(
            select(Book)
            .options(selectinload(Book.genres))
            .order_by(Book.id)
        )
    )


def search_books(
    session: Session,
    genre_id: int | None = None,
    publication_year: int | None = None,
    title_part: str | None = None,
) -> list[Book]:
    stmt = select(Book).options(selectinload(Book.genres))
    if genre_id is not None:
        stmt = stmt.where(Book.genres.any(Genre.id == genre_id))
    if publication_year is not None:
        stmt = stmt.where(Book.publication_year == publication_year)
    if title_part:
        stmt = stmt.where(Book.title.ilike(f"%{title_part}%"))
    return list(session.scalars(stmt.order_by(Book.title)))


def update_book(session: Session, book_id: int, **changes) -> Book | None:
    obj = session.get(Book, book_id)
    if obj is None:
        return None
    genres = changes.pop("genres", None)
    for key, value in changes.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    if genres is not None:
        obj.genres = genres
    session.flush()
    return obj


def delete_book(session: Session, book_id: int) -> bool:
    obj = session.get(Book, book_id)
    if obj is None:
        return False
    session.delete(obj)
    session.flush()
    return True


# ---------- Избранное ----------

def add_favorite(session: Session, user_id: int, book_id: int) -> Favorite:
    existing = session.get(Favorite, (user_id, book_id))
    if existing:
        return existing
    obj = Favorite(user_id=user_id, book_id=book_id)
    session.add(obj)
    session.flush()
    return obj


def list_favorites(session: Session, user_id: int) -> list[Favorite]:
    return list(
        session.scalars(
            select(Favorite)
            .options(selectinload(Favorite.book))
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )
    )


def remove_favorite(session: Session, user_id: int, book_id: int) -> bool:
    obj = session.get(Favorite, (user_id, book_id))
    if obj is None:
        return False
    session.delete(obj)
    session.flush()
    return True


# ---------- Отзывы ----------

def create_review(
    session: Session,
    user_id: int,
    book_id: int,
    rating: int,
    comment: str | None = None,
) -> Review:
    obj = Review(
        user_id=user_id,
        book_id=book_id,
        rating=rating,
        comment=comment,
    )
    session.add(obj)
    session.flush()
    return obj


def list_reviews_for_book(session: Session, book_id: int) -> list[Review]:
    return list(
        session.scalars(
            select(Review)
            .where(Review.book_id == book_id)
            .order_by(Review.created_at.desc())
        )
    )


def update_review(session: Session, review_id: int, **changes) -> Review | None:
    obj = session.get(Review, review_id)
    if obj is None:
        return None
    for key, value in changes.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    session.flush()
    return obj


def delete_review(session: Session, review_id: int) -> bool:
    obj = session.get(Review, review_id)
    if obj is None:
        return False
    session.delete(obj)
    session.flush()
    return True


# ---------- Прогресс чтения ----------

def get_progress(session: Session, user_id: int, book_id: int) -> ReadingProgress | None:
    return session.get(ReadingProgress, (user_id, book_id))


def save_progress(
    session: Session, user_id: int, book_id: int, last_page: int
) -> ReadingProgress:
    obj = session.get(ReadingProgress, (user_id, book_id))
    if obj is None:
        obj = ReadingProgress(
            user_id=user_id, book_id=book_id, last_page=last_page
        )
        session.add(obj)
    else:
        obj.last_page = last_page
    session.flush()
    return obj
