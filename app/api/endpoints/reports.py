from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated, Dict, Optional, List
from datetime import date, datetime, timedelta
from calendar import monthrange

from app.db.mongodb import get_database
from app.core.deps import get_current_user
from app.crud.transaction import get_transaction_stats
from app.models.transaction import TransactionType
from app.models.user import Currency

router = APIRouter()


@router.get("/monthly")
async def get_monthly_report(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)],
    year: int = Query(..., description="Год отчета"),
    month: int = Query(..., ge=1, le=12, description="Месяц отчета (1-12)"),
    currency: Currency = Query(Currency.RUB, description="Валюта отчета")
):
    """
    Получение ежемесячного отчета по финансам
    """
    # Проверяем корректность даты
    try:
        start_date = datetime(year, month, 1)
        _, days_in_month = monthrange(year, month)
        end_date = datetime(year, month, days_in_month, 23, 59, 59)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректная дата"
        )
    
    # Формируем базовый запрос
    match_query = {
        "user_id": current_user["id"],
        "date": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    if currency:
        match_query["currency"] = currency
    
    # Статистика по доходам
    income_pipeline = [
        {"$match": {**match_query, "type": TransactionType.INCOME}},
        {"$group": {
            "_id": {"$dayOfMonth": "$date"},
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    # Статистика по расходам
    expense_pipeline = [
        {"$match": {**match_query, "type": TransactionType.EXPENSE}},
        {"$group": {
            "_id": {"$dayOfMonth": "$date"},
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    # Топ категорий по расходам
    top_expense_categories = [
        {"$match": {**match_query, "type": TransactionType.EXPENSE}},
        {"$lookup": {
            "from": "categories",
            "localField": "category_id",
            "foreignField": "_id",
            "as": "category"
        }},
        {"$unwind": "$category"},
        {"$group": {
            "_id": "$category_id",
            "name": {"$first": "$category.name"},
            "icon": {"$first": "$category.icon"},
            "color": {"$first": "$category.color"},
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total": -1}},
        {"$limit": 5}
    ]
    
    # Топ категорий по доходам
    top_income_categories = [
        {"$match": {**match_query, "type": TransactionType.INCOME}},
        {"$lookup": {
            "from": "categories",
            "localField": "category_id",
            "foreignField": "_id",
            "as": "category"
        }},
        {"$unwind": "$category"},
        {"$group": {
            "_id": "$category_id",
            "name": {"$first": "$category.name"},
            "icon": {"$first": "$category.icon"},
            "color": {"$first": "$category.color"},
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total": -1}},
        {"$limit": 5}
    ]
    
    # Выполняем запросы асинхронно
    daily_income = await db.transactions.aggregate(income_pipeline).to_list(length=100)
    daily_expense = await db.transactions.aggregate(expense_pipeline).to_list(length=100)
    expense_categories = await db.transactions.aggregate(top_expense_categories).to_list(length=5)
    income_categories = await db.transactions.aggregate(top_income_categories).to_list(length=5)
    
    # Преобразуем ID категорий в строки
    for cat in expense_categories:
        cat["id"] = str(cat["_id"])
        del cat["_id"]
    
    for cat in income_categories:
        cat["id"] = str(cat["_id"])
        del cat["_id"]
    
    # Подсчитываем итоги
    total_income = sum(day["total"] for day in daily_income)
    total_expense = sum(day["total"] for day in daily_expense)
    balance = total_income - total_expense
    
    # Формируем дневную статистику в виде словаря
    daily_stats = {}
    for day in range(1, days_in_month + 1):
        daily_stats[day] = {
            "income": 0,
            "expense": 0,
            "balance": 0
        }
    
    for day in daily_income:
        day_num = day["_id"]
        daily_stats[day_num]["income"] = day["total"]
        daily_stats[day_num]["balance"] = daily_stats[day_num]["income"] - daily_stats[day_num]["expense"]
    
    for day in daily_expense:
        day_num = day["_id"]
        daily_stats[day_num]["expense"] = day["total"]
        daily_stats[day_num]["balance"] = daily_stats[day_num]["income"] - daily_stats[day_num]["expense"]
    
    return {
        "year": year,
        "month": month,
        "currency": currency,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "daily_stats": daily_stats,
        "top_expense_categories": expense_categories,
        "top_income_categories": income_categories
    }


@router.get("/income-expense")
async def get_income_expense_report(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)],
    period: str = Query("month", description="Период отчета (week, month, year)"),
    currency: Currency = Query(Currency.RUB, description="Валюта отчета")
):
    """
    Получение отчета по доходам и расходам за период
    """
    stats = await get_transaction_stats(db, current_user["id"], period, currency)
    
    return {
        "period": period,
        "currency": currency,
        "start_date": stats["start_date"],
        "end_date": stats["end_date"],
        "income": {
            "total": sum(item["total"] for item in stats["income"]["by_currency"] if item["_id"] == currency),
            "by_category": stats["income"]["by_category"]
        },
        "expense": {
            "total": sum(item["total"] for item in stats["expense"]["by_currency"] if item["_id"] == currency),
            "by_category": stats["expense"]["by_category"]
        }
    }


@router.get("/category")
async def get_category_report(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)],
    category_type: TransactionType = Query(..., description="Тип категорий (income или expense)"),
    period: str = Query("month", description="Период отчета (week, month, year)"),
    currency: Currency = Query(Currency.RUB, description="Валюта отчета")
):
    """
    Получение отчета по категориям указанного типа за период
    """
    stats = await get_transaction_stats(db, current_user["id"], period, currency)
    
    if category_type == TransactionType.INCOME:
        category_stats = stats["income"]["by_category"]
        total = sum(item["total"] for item in stats["income"]["by_currency"] if item["_id"] == currency)
    else:
        category_stats = stats["expense"]["by_category"]
        total = sum(item["total"] for item in stats["expense"]["by_currency"] if item["_id"] == currency)
    
    # Добавляем процент от общей суммы
    if total > 0:
        for cat in category_stats:
            if cat["currency"] == currency:
                cat["percentage"] = round((cat["total"] / total) * 100, 2)
            else:
                cat["percentage"] = 0
    
    return {
        "period": period,
        "currency": currency,
        "type": category_type,
        "start_date": stats["start_date"],
        "end_date": stats["end_date"],
        "total": total,
        "categories": category_stats
    } 