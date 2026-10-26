from fastapi import APIRouter, Depends, status
from app.dependencies import get_library_service, get_current_user
from app.models import User
from app.schemas import UserRegisterIn, UserLoginIn, UserOut, TokenOut
from app.services import LibraryService

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    data: UserRegisterIn,
    service: LibraryService = Depends(get_library_service),
):
    return service.register_user(data)


@router.post("/login", response_model=TokenOut)
def login(
    data: UserLoginIn,
    service: LibraryService = Depends(get_library_service),
):
    token = service.authenticate_user(data)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user