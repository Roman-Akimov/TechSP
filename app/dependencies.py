import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import User
from app.security import decode_access_token
from app.services import LibraryService

security_scheme = HTTPBearer()


def get_library_service(session: Session = Depends(get_session)) -> LibraryService:
    return LibraryService(session=session)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: Session = Depends(get_session),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", 0))
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или просроченный JWT-токен",
        )

    stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
    user = session.scalar(stmt)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или деактивирован",
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.code != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: требуются права администратора (admin)",
        )
    return current_user