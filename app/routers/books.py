from fastapi import APIRouter, Depends, Query, status, Response
from app.dependencies import get_library_service, require_admin
from app.models import User
from app.schemas import BookCreateIn, BookUpdateIn, BookOut
from app.services import LibraryService

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookOut])
def list_books(
    genre: str | None = Query(default=None, description="Фильтр по названию жанра"),
    language: str | None = Query(default=None, description="Фильтр по коду языка (ru, en)"),
    service: LibraryService = Depends(get_library_service),
):
    return service.list_books(genre_name=genre, language=language)


@router.get("/{book_id}", response_model=BookOut)
def get_book(
    book_id: int,
    service: LibraryService = Depends(get_library_service),
):
    return service.get_book_or_404(book_id)


@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(
    data: BookCreateIn,
    service: LibraryService = Depends(get_library_service),
    _admin: User = Depends(require_admin),
):
    return service.create_book(data)


@router.put("/{book_id}", response_model=BookOut)
def update_book(
    book_id: int,
    data: BookUpdateIn,
    service: LibraryService = Depends(get_library_service),
    _admin: User = Depends(require_admin),
):
    return service.update_book(book_id, data)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    service: LibraryService = Depends(get_library_service),
    _admin: User = Depends(require_admin),
):
    service.delete_book(book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)