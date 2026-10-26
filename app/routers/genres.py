from fastapi import APIRouter, Depends, status
from app.dependencies import get_library_service, require_admin
from app.models import User
from app.schemas import GenreCreateIn, GenreOut
from app.services import LibraryService

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=list[GenreOut])
def list_genres(service: LibraryService = Depends(get_library_service)):
    return service.list_genres()


@router.post("", response_model=GenreOut, status_code=status.HTTP_201_CREATED)
def create_genre(
    data: GenreCreateIn,
    service: LibraryService = Depends(get_library_service),
    _admin: User = Depends(require_admin),
):
    return service.create_genre(data)