from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.auth import TokenData

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хешу
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Создает хеш пароля
    """
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT токен доступа
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Проверяет токен и возвращает данные пользователя
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if datetime.fromtimestamp(payload.get("exp")) < datetime.now():
            return None
        return payload
    except (jwt.JWTError, ValidationError):
        return None


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(
            user_id=user_id,
            username=payload.get("username"),
            email=payload.get("email"),
            role=payload.get("role")
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) 