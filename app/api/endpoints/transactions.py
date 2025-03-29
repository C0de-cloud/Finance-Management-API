from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated, List, Dict, Optional, Any
from datetime import date, datetime

from app.db.mongodb import get_database
from app.core.deps import get_current_user, transaction_filter_params, pagination_params
from app.crud.transaction import (
    get_transactions, 
    get_transaction_by_id, 
    create_transaction, 
    update_transaction, 
    delete_transaction,
    get_transaction_stats
)
from app.models.transaction import (
    Transaction, 
    TransactionCreate, 
    TransactionUpdate, 
    TransactionWithCategory, 
    TransactionType,
    TransactionStatistics
)
from app.models.user import Currency

router = APIRouter()


@router.get("", response_model=List[Transaction])
async def read_transactions(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)],
    filters: Annotated[Dict, Depends(transaction_filter_params)],
    pagination: Annotated[Dict, Depends(pagination_params)],
    sort_by: str = Query("date", description="Поле для сортировки (date, amount)"),
    sort_order: int = Query(-1, description="Порядок сортировки (-1 - по убыванию, 1 - по возрастанию)")
):
    """
    Получение списка транзакций с фильтрацией и пагинацией
    """
    transactions = await get_transactions(
        db, 
        current_user["id"], 
        skip=pagination["offset"], 
        limit=pagination["limit"],
        **filters,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return transactions


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_new_transaction(
    transaction_data: TransactionCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Создание новой транзакции
    """
    return await create_transaction(db, transaction_data, current_user["id"])


@router.get("/stats", response_model=TransactionStatistics)
async def read_transaction_statistics(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)],
    period: str = Query("month", description="Период статистики (week, month, year)"),
    currency: Optional[Currency] = Query(None, description="Валюта для статистики")
):
    """
    Получение статистики по транзакциям
    """
    return await get_transaction_stats(
        db, 
        current_user["id"], 
        period=period, 
        currency=currency
    )


@router.get("/{transaction_id}", response_model=Transaction)
async def read_transaction(
    transaction_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Получение информации о транзакции по ID
    """
    transaction = await get_transaction_by_id(db, transaction_id, current_user["id"])
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    return transaction


@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction_by_id(
    transaction_id: str,
    transaction_data: TransactionUpdate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Обновление транзакции
    """
    updated_transaction = await update_transaction(
        db, 
        transaction_id, 
        transaction_data, 
        current_user["id"]
    )
    if not updated_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    return updated_transaction


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction_by_id(
    transaction_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Удаление транзакции
    """
    success = await delete_transaction(db, transaction_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    return 