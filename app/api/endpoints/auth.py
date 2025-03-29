from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated

from app.db.mongodb import get_database
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.deps import get_current_user
from app.crud.user import authenticate_user, create_user, get_user_by_email, change_user_password
from app.models.auth import Token, LoginInput, PasswordChange, ResetPasswordRequest, ResetPasswordConfirm
from app.models.user import UserCreate

settings = get_settings()
router = APIRouter()


@router.post("/register", response_model=Token)
async def register_user(
    user_data: UserCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Регистрация нового пользователя
    """
    user = await create_user(db, user_data)
    access_token = create_access_token(
        subject=user["id"]
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginInput,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Авторизация пользователя и получение токена
    """
    user = await authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        subject=user["id"]
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    OAuth2 совместимый токен, для совместимости с OpenAPI
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        subject=user["id"]
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/password/change", status_code=200)
async def change_password(
    password_data: PasswordChange,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Смена пароля текущего пользователя
    """
    success = await change_user_password(
        db, 
        current_user["id"], 
        password_data.current_password, 
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текущий пароль неверен"
        )
    
    return {"message": "Пароль успешно изменен"}


@router.post("/password/reset/request", status_code=200)
async def request_password_reset(
    reset_data: ResetPasswordRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Запрос на сброс пароля (отправка токена на email)
    """
    user = await get_user_by_email(db, reset_data.email)
    if not user:
        # Не сообщаем, что пользователь не найден для безопасности
        return {"message": "Если пользователь с таким email существует, инструкции по сбросу пароля были отправлены"}
    
    # В реальном приложении здесь бы генерировался токен и отправлялся email
    # Для демонстрации просто возвращаем положительный ответ
    
    return {"message": "Инструкции по сбросу пароля отправлены на email"}


@router.post("/password/reset/confirm", status_code=200)
async def confirm_password_reset(
    reset_data: ResetPasswordConfirm,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Подтверждение сброса пароля с использованием токена
    """
    # В реальном приложении здесь бы проверялся токен и выполнялся сброс пароля
    # Для демонстрации просто возвращаем положительный ответ
    
    return {"message": "Пароль успешно изменен"} 