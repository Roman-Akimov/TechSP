from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# роли и пользователи
class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str


class UserRegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100, description="Пароль минимум 6 символов")
    full_name: str = Field(min_length=2, max_length=200)
    role_code: str = Field(default="reader", pattern=r"^(reader|admin)$")


class UserLoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    role: RoleOut
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# жанры
class GenreCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None


class GenreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


# книжки
class BookCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    isbn: str | None = Field(default=None, max_length=20)
    description: str | None = None
    publication_year: int | None = Field(default=None, ge=0, le=2100)
    publisher: str | None = Field(default=None, max_length=150)
    cover_url: str | None = Field(default=None, max_length=500)
    file_url: str = Field(min_length=1, max_length=500)
    total_pages: int = Field(gt=0)
    language: str = Field(default="ru", max_length=10)
    genre_ids: list[int] = Field(default_factory=list)


class BookUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    isbn: str | None = Field(default=None, max_length=20)
    description: str | None = None
    publication_year: int | None = Field(default=None, ge=0, le=2100)
    publisher: str | None = Field(default=None, max_length=150)
    cover_url: str | None = Field(default=None, max_length=500)
    file_url: str | None = Field(default=None, min_length=1, max_length=500)
    total_pages: int | None = Field(default=None, gt=0)
    language: str | None = Field(default=None, max_length=10)
    genre_ids: list[int] | None = None


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    isbn: str | None
    description: str | None
    publication_year: int | None
    publisher: str | None
    cover_url: str | None
    file_url: str
    total_pages: int | None
    language: str
    genres: list[GenreOut] = []
    created_at: datetime


# прогресс чтения
class ProgressUpdateIn(BaseModel):
    last_page: int = Field(ge=1, description="Номер текущей страницы")


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    book_id: int
    last_page: int
    percent: Decimal
    updated_at: datetime


# отзывы
class ReviewCreateIn(BaseModel):
    rating: int = Field(ge=1, le=5, description="Оценка от 1 до 5")
    comment: str | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book_id: int
    rating: int
    comment: str | None
    created_at: datetime