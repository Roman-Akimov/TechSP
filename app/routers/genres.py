from fastapi import APIRouter, Depends, Response, status
from app.dependencies import get_library_service, require_admin
from app.models import User
from app.schemas import GenreCreateIn, GenreOut
from app.services import LibraryService

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=list[GenreOut])
def list_genres(service: LibraryService = Depends(get_library_service)):
    return service.list_genres()


@router.get("/{genre_id}", response_model=GenreOut)
def get_genre(genre_id: int, service: LibraryService = Depends(get_library_service)):
    return service.get_genre_or_404(genre_id)


@router.post("", response_model=GenreOut, status_code=status.HTTP_201_CREATED)
def create_genre(
    data: GenreCreateIn,
    service: LibraryService = Depends(get_library_service),
    _admin: User = Depends(require_admin),
):
    return service.create_genre(data)


@router.put("/{genre_id}", response_model=GenreOut)
def update_genre(
    genre_id: int,
    data: GenreCreateIn,
    service: LibraryService = Depends(get_library_service),
    _admin: User = Depends(require_admin),
):
    return service.update_genre(genre_id, data)


@router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_genre(
    genre_id: int,
    service: LibraryService = Depends(get_library_service),
    _admin: User = Depends(require_admin),
):
    service.delete_genre(genre_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)