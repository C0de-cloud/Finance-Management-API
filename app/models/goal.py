from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, date

from app.models.user import Currency


class GoalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    currency: Currency
    current_amount: float = Field(default=0, ge=0)
    deadline: Optional[date] = None
    description: Optional[str] = None

    @validator("current_amount")
    def current_amount_less_than_target(cls, v, values):
        if "target_amount" in values and v > values["target_amount"]:
            raise ValueError("Current amount must be less than or equal to target amount")
        return v


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_amount: Optional[float] = Field(None, gt=0)
    currency: Optional[Currency] = None
    current_amount: Optional[float] = Field(None, ge=0)
    deadline: Optional[date] = None
    description: Optional[str] = None


class Goal(GoalBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_completed: bool = False


class GoalList(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[Goal]


class GoalProgress(BaseModel):
    id: str
    name: str
    target_amount: float
    current_amount: float
    currency: Currency
    remaining: float
    percentage_completed: float
    days_left: Optional[int] = None
    estimated_completion_date: Optional[date] = None


class GoalContribution(BaseModel):
    amount: float = Field(..., gt=0)
    date: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    transaction_id: Optional[str] = None 