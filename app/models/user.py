from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator


class UserRole(str, Enum):
    """Роль пользователя в системе"""
    USER = "user"           # Обычный пользователь
    ADMIN = "admin"         # Администратор


class Currency(str, Enum):
    """Поддерживаемые валюты"""
    RUB = "RUB"             # Российский рубль
    USD = "USD"             # Доллар США
    EUR = "EUR"             # Евро
    GBP = "GBP"             # Фунт стерлингов
    CNY = "CNY"             # Китайский юань
    JPY = "JPY"             # Японская йена
    KZT = "KZT"             # Казахстанский тенге
    BYN = "BYN"             # Белорусский рубль


class UserBase(BaseModel):
    """Базовая модель пользователя"""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Имя пользователя (используется для входа)"
    )
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Полное имя пользователя")
    default_currency: Currency = Field(default=Currency.RUB, description="Валюта пользователя по умолчанию")


class UserCreate(UserBase):
    """Модель для создания пользователя"""
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        description="Пароль пользователя"
    )
    
    @validator('password')
    def password_validator(cls, v):
        """Валидатор пароля на сложность"""
        # Пароль должен содержать хотя бы одну цифру и одну букву
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not any(c.isalpha() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну букву")
        return v


class UserUpdate(BaseModel):
    """Модель для обновления пользователя"""
    email: Optional[EmailStr] = Field(None, description="Электронная почта пользователя")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Полное имя пользователя")
    default_currency: Optional[Currency] = Field(None, description="Валюта пользователя по умолчанию")
    username: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=50, 
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Имя пользователя"
    )


class User(UserBase):
    """Полная модель пользователя"""
    id: str = Field(..., description="Уникальный идентификатор пользователя")
    role: UserRole = Field(default=UserRole.USER, description="Роль пользователя")
    created_at: datetime = Field(..., description="Дата и время регистрации пользователя")
    updated_at: datetime = Field(..., description="Дата и время последнего обновления профиля")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class UserWithStats(User):
    """Пользователь со статистикой по финансам"""
    total_income: float = Field(default=0, description="Общий доход пользователя")
    total_expense: float = Field(default=0, description="Общие расходы пользователя")
    balance: float = Field(default=0, description="Текущий баланс пользователя")
    month_income: float = Field(default=0, description="Доход за текущий месяц")
    month_expense: float = Field(default=0, description="Расходы за текущий месяц")
    month_balance: float = Field(default=0, description="Баланс за текущий месяц")
    top_expense_categories: List[dict] = Field(default_factory=list, description="Топ-5 категорий расходов")
    top_income_categories: List[dict] = Field(default_factory=list, description="Топ-5 категорий доходов")
    recent_transactions: List[dict] = Field(default_factory=list, description="Последние транзакции") 