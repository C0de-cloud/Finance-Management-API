from typing import Optional
from pydantic import BaseModel, Field

from app.models.user import UserRole


class Token(BaseModel):
    """Модель токена доступа"""
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field(default="bearer", description="Тип токена")


class TokenData(BaseModel):
    """Данные, хранящиеся в токене"""
    user_id: str = Field(..., description="ID пользователя")
    username: Optional[str] = Field(None, description="Имя пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")
    role: Optional[str] = Field(None, description="Роль пользователя")


class LoginInput(BaseModel):
    """Данные для входа в систему"""
    username: str = Field(..., description="Имя пользователя или email")
    password: str = Field(..., description="Пароль пользователя")
    

class PasswordChange(BaseModel):
    """Данные для смены пароля"""
    current_password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(
        ..., 
        min_length=8,
        max_length=100,
        description="Новый пароль"
    )
    

class ResetPasswordRequest(BaseModel):
    """Запрос на сброс пароля"""
    email: str = Field(..., description="Email пользователя для сброса пароля")
    

class ResetPasswordConfirm(BaseModel):
    """Подтверждение сброса пароля"""
    token: str = Field(..., description="Токен для сброса пароля")
    new_password: str = Field(
        ..., 
        min_length=8,
        max_length=100,
        description="Новый пароль"
    ) 