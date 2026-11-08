from fastapi import APIRouter, Depends, Response, status, HTTPException
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
from app.db import get_session
from app.models import Book, BookGenre, Favorite, Review
from app.grpc_client import get_recommendations
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
import grpc
import logging

log = logging.getLogger("library-api")

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


@router.get("/progress/{book_id}", response_model=ProgressOut)
def get_progress(
    book_id: int,
    current_user: User = Depends(get_current_user),
    service: LibraryService = Depends(get_library_service),
):
    return service.get_reading_progress(current_user.id, book_id)


@router.put("/progress/{book_id}", response_model=ProgressOut)
def save_progress(
    book_id: int,
    data: ProgressUpdateIn,
    current_user: User = Depends(get_current_user),
    service: LibraryService = Depends(get_library_service),
):
    return service.save_reading_progress(current_user.id, book_id, data)


@router.get("/reviews/{book_id}", response_model=list[ReviewOut])
def list_reviews(
    book_id: int,
    service: LibraryService = Depends(get_library_service),
):
    return service.list_book_reviews(book_id)


@router.post("/reviews/{book_id}", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def upsert_review(
    book_id: int,
    data: ReviewCreateIn,
    current_user: User = Depends(get_current_user),
    service: LibraryService = Depends(get_library_service),
):
    return service.add_or_update_review(current_user.id, book_id, data)


@router.delete("/reviews/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_review(
    book_id: int,
    current_user: User = Depends(get_current_user),
    service: LibraryService = Depends(get_library_service),
):
    service.delete_user_review(current_user.id, book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/recommendations")
def get_recommended_books(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Персональные рекомендации, ранжируемые отдельным gRPC-микросервисом."""
    limit = max(1, min(limit, 50))
    log.info("[API] Пользователь %s запросил рекомендации", current_user.id)

    favorite_rows = session.execute(
        select(Favorite.book_id).where(Favorite.user_id == current_user.id)
    ).all()
    favorite_ids = [row[0] for row in favorite_rows]

    preferred_genre_ids = set()
    if favorite_ids:
        genre_rows = session.execute(
            select(BookGenre.genre_id).where(BookGenre.book_id.in_(favorite_ids))
        ).all()
        preferred_genre_ids.update(row[0] for row in genre_rows)

    stmt = select(Book).options(selectinload(Book.genres)).order_by(Book.id)
    if favorite_ids:
        stmt = stmt.where(~Book.id.in_(favorite_ids))
    books = list(session.scalars(stmt).all())

    rating_rows = session.execute(
        select(Review.book_id, func.avg(Review.rating))
        .group_by(Review.book_id)
    ).all()
    ratings = {book_id: float(avg_rating) for book_id, avg_rating in rating_rows}

    candidates = [
        {
            "id": book.id,
            "title": book.title,
            "genre_ids": [genre.id for genre in book.genres],
            "average_rating": ratings.get(book.id, 0.0),
        }
        for book in books
    ]
    try:
        recommendations = get_recommendations(
            sorted(preferred_genre_ids), candidates, limit
        )
    except grpc.RpcError as exc:
        log.exception("[API] Ошибка обращения к gRPC-сервису")
        raise HTTPException(
            status_code=503,
            detail="Сервис рекомендаций временно недоступен",
        ) from exc

    result = []
    for recommendation in recommendations:
        book = next((item for item in books if item.id == recommendation["id"]), None)
        if book:
            result.append({
                "book": {
                    "id": book.id,
                    "title": book.title,
                    "description": book.description,
                    "publication_year": book.publication_year,
                    "publisher": book.publisher,
                    "cover_url": book.cover_url,
                    "file_url": book.file_url,
                    "total_pages": book.total_pages,
                    "language": book.language,
                    "genres": [{"id": g.id, "name": g.name, "description": g.description}
                               for g in book.genres],
                },
                "score": recommendation["score"],
                "reason": recommendation["reason"],
            })
    log.info("[API] Пользователю %s возвращено рекомендаций: %d",
             current_user.id, len(result))
    return {"user_id": current_user.id, "recommendations": result}
