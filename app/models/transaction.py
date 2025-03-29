from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, validator, confloat

from app.models.user import Currency


class TransactionType(str, Enum):
    """Тип транзакции"""
    INCOME = "income"       # Доход
    EXPENSE = "expense"     # Расход


class TransactionBase(BaseModel):
    """Базовая модель транзакции"""
    type: TransactionType = Field(..., description="Тип транзакции (доход или расход)")
    amount: confloat(gt=0) = Field(..., description="Сумма транзакции")
    currency: Currency = Field(..., description="Валюта транзакции")
    description: Optional[str] = Field(None, max_length=500, description="Описание транзакции")
    date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Дата и время транзакции")
    category_id: str = Field(..., description="ID категории транзакции")


class TransactionCreate(TransactionBase):
    """Модель для создания транзакции"""
    pass


class TransactionUpdate(BaseModel):
    """Модель для обновления транзакции"""
    type: Optional[TransactionType] = Field(None, description="Тип транзакции (доход или расход)")
    amount: Optional[confloat(gt=0)] = Field(None, description="Сумма транзакции")
    currency: Optional[Currency] = Field(None, description="Валюта транзакции")
    description: Optional[str] = Field(None, max_length=500, description="Описание транзакции")
    date: Optional[datetime] = Field(None, description="Дата и время транзакции")
    category_id: Optional[str] = Field(None, description="ID категории транзакции")


class Transaction(TransactionBase):
    """Полная модель транзакции"""
    id: str = Field(..., description="Уникальный идентификатор транзакции")
    user_id: str = Field(..., description="ID пользователя-владельца")
    created_at: datetime = Field(..., description="Дата и время создания записи")
    updated_at: datetime = Field(..., description="Дата и время последнего обновления записи")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class TransactionWithCategory(Transaction):
    """Транзакция с информацией о категории"""
    category_name: str = Field(..., description="Название категории")
    category_icon: str = Field(..., description="Иконка категории")
    category_color: str = Field(..., description="Цвет категории")


class TransactionStatistics(BaseModel):
    """Статистика по транзакциям"""
    period: str = Field(..., description="Период статистики (week, month, year)")
    start_date: datetime = Field(..., description="Начальная дата периода")
    end_date: datetime = Field(..., description="Конечная дата периода")
    income: dict = Field(..., description="Статистика по доходам")
    expense: dict = Field(..., description="Статистика по расходам")


class TransactionCategory(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None


class TransactionList(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[Transaction]


class MonthlyTransactionSummary(BaseModel):
    month: int
    year: int
    total_income: float
    total_expense: float
    balance: float
    currency: Currency
    transactions_count: int
    top_categories: List[dict]


class CategoryTransactionSummary(BaseModel):
    category_id: str
    category_name: str
    total_amount: float
    currency: Currency
    transaction_count: int
    percentage: float 