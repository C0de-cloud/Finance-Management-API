from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, date

from app.models.user import Currency


class BudgetPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class BudgetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    currency: Currency
    period: BudgetPeriod
    category_id: Optional[str] = None
    start_date: date
    end_date: date
    description: Optional[str] = None

    @validator("end_date")
    def end_date_after_start_date(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[Currency] = None
    period: Optional[BudgetPeriod] = None
    category_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class BudgetCategory(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None


class Budget(BudgetBase):
    id: str
    user_id: str
    category: Optional[BudgetCategory] = None
    created_at: datetime
    updated_at: datetime


class BudgetList(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[Budget]


class BudgetProgress(BaseModel):
    id: str
    name: str
    amount: float
    currency: Currency
    spent: float
    remaining: float
    percentage_used: float
    days_left: int
    is_active: bool 