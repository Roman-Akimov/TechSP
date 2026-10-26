from fastapi import APIRouter, Depends, status
from app.dependencies import get_library_service, get_current_user
from app.models import User
from app.schemas import (
    BookOut,
    ProgressUpdateIn,
    ProgressOut,
    ReviewCreateIn,
    ReviewOut,
)
from app.services import LibraryService

router = APIRouter(tags=["reader-actions"])


@router.get("/favorites", response_model=list[BookOut])
def get_my_favorites(
    current_user: User = Depends(get_current_user),
    service: LibraryService = Depends(get_library_service),
):
    return service.get_user_favorites(current_user.id)


@router.post("/favorites/{book_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(
    book_id: int,
    current_user: User = Depends(get_current_user),
    service: LibraryService = Depends(get_library_service),
):
    service.add_to_favorites(current_user.id, book_id)
    return {"message": "Книга добавлена в избранное", "book_id": book_id}


@router.delete("/favorites/{book_id}")
def remove_favorite(
    book_id: int,
    current_user: User = Depends(get_current_user),
    service: LibraryService = Depends(get_library_service),
):
    service.remove_from_favorites(current_user.id, book_id)
    return {"message": "Книга удалена из избранного", "book_id": book_id}


@router.put("/progress/{book_id}", response_model=ProgressOut)
def save_progress(
    book_id: int,
    data: ProgressUpdateIn,
    current_user: User = Depends(get_current_user),
    service: LibraryService = Depends(get_library_service),
):
    return service.save_reading_progress(current_user.id, book_id, data)


@router.post("/reviews/{book_id}", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def upsert_review(
    book_id: int,
    data: ReviewCreateIn,
    current_user: User = Depends(get_current_user),
    service: LibraryService = Depends(get_library_service),
):
    return service.add_or_update_review(current_user.id, book_id, data)