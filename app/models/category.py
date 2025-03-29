from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from app.models.transaction import TransactionType


class CategoryBase(BaseModel):
    """Базовая модель категории"""
    name: str = Field(..., min_length=1, max_length=50, description="Название категории")
    type: TransactionType = Field(..., description="Тип категории (расход или доход)")
    icon: str = Field(default="circle", description="Название иконки для категории")
    color: str = Field(default="#3f51b5", description="Цвет категории в HEX формате")


class CategoryCreate(CategoryBase):
    """Модель для создания категории"""
    pass


class CategoryUpdate(BaseModel):
    """Модель для обновления категории"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Название категории")
    icon: Optional[str] = Field(None, description="Название иконки для категории")
    color: Optional[str] = Field(None, description="Цвет категории в HEX формате")
    
    @validator('color')
    def validate_color(cls, v):
        if v and not v.startswith('#'):
            return f"#{v}"
        return v


class Category(CategoryBase):
    """Полная модель категории"""
    id: str = Field(..., description="Уникальный идентификатор категории")
    user_id: str = Field(..., description="ID пользователя-владельца")
    is_default: bool = Field(default=False, description="Флаг системной категории")
    created_at: datetime = Field(..., description="Дата и время создания категории")
    updated_at: datetime = Field(..., description="Дата и время последнего обновления категории")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class CategoryWithStats(Category):
    """Модель категории со статистикой использования"""
    stats: dict = Field(default_factory=dict, description="Статистика использования категории")
    recent_transactions: List[dict] = Field(default_factory=list, description="Последние транзакции в категории")


class CategoryList(BaseModel):
    total: int
    items: List[Category]


class CategoryStatistics(BaseModel):
    id: str
    name: str
    type: TransactionType
    total_amount: float
    transaction_count: int
    percentage: float 