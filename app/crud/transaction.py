from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from fastapi import HTTPException, status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.transaction import TransactionCreate, TransactionUpdate, TransactionType


async def get_transactions(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    skip: int = 0, 
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category_id: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None,
    currency: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    sort_by: str = "date",
    sort_order: int = -1
) -> List[Dict[str, Any]]:
    """
    Получает список транзакций с фильтрацией
    """
    # Строим запрос с фильтрацией
    query = {"user_id": user_id}
    
    if start_date:
        query["date"] = query.get("date", {})
        query["date"]["$gte"] = start_date
    
    if end_date:
        query["date"] = query.get("date", {})
        query["date"]["$lte"] = end_date
    
    if category_id:
        query["category_id"] = category_id
    
    if transaction_type:
        query["type"] = transaction_type
    
    if currency:
        query["currency"] = currency
    
    if min_amount:
        query["amount"] = query.get("amount", {})
        query["amount"]["$gte"] = min_amount
    
    if max_amount:
        query["amount"] = query.get("amount", {})
        query["amount"]["$lte"] = max_amount
    
    # Определяем сортировку
    sort_field = sort_by if sort_by in ["date", "amount"] else "date"
    
    # Получаем данные из базы
    transactions = await db.transactions.find(query).sort(
        [(sort_field, sort_order)]
    ).skip(skip).limit(limit).to_list(length=limit)
    
    # Преобразуем ObjectId в строки для JSON сериализации
    for transaction in transactions:
        transaction["id"] = str(transaction["_id"])
        del transaction["_id"]
    
    return transactions


async def get_transaction_by_id(
    db: AsyncIOMotorDatabase, 
    transaction_id: str, 
    user_id: str
) -> Optional[Dict[str, Any]]:
    """
    Получает транзакцию по ID
    """
    try:
        transaction = await db.transactions.find_one(
            {"_id": ObjectId(transaction_id), "user_id": user_id}
        )
    except:
        return None
    
    if not transaction:
        return None
    
    transaction["id"] = str(transaction["_id"])
    del transaction["_id"]
    
    return transaction


async def create_transaction(
    db: AsyncIOMotorDatabase, 
    transaction_data: TransactionCreate, 
    user_id: str
) -> Dict[str, Any]:
    """
    Создает новую транзакцию
    """
    # Проверяем существование категории
    try:
        category = await db.categories.find_one({
            "_id": ObjectId(transaction_data.category_id),
            "user_id": user_id
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат ID категории"
        )
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем соответствие типа транзакции и категории
    if transaction_data.type != category["type"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип транзакции ({transaction_data.type}) не соответствует типу категории ({category['type']})"
        )
    
    # Создаем транзакцию
    transaction_dict = transaction_data.model_dump()
    now = datetime.utcnow()
    
    # Если дата не указана, используем текущую
    if "date" not in transaction_dict or not transaction_dict["date"]:
        transaction_dict["date"] = now
    
    transaction_dict["user_id"] = user_id
    transaction_dict["created_at"] = now
    transaction_dict["updated_at"] = now
    
    result = await db.transactions.insert_one(transaction_dict)
    
    return await get_transaction_by_id(db, str(result.inserted_id), user_id)


async def update_transaction(
    db: AsyncIOMotorDatabase, 
    transaction_id: str, 
    transaction_data: TransactionUpdate, 
    user_id: str
) -> Optional[Dict[str, Any]]:
    """
    Обновляет существующую транзакцию
    """
    transaction = await get_transaction_by_id(db, transaction_id, user_id)
    
    if not transaction:
        return None
    
    update_data = {k: v for k, v in transaction_data.model_dump(exclude_unset=True).items() if v is not None}
    
    # Если меняется категория, проверяем ее существование и совместимость типов
    if "category_id" in update_data and update_data["category_id"] != transaction["category_id"]:
        try:
            category = await db.categories.find_one({
                "_id": ObjectId(update_data["category_id"]),
                "user_id": user_id
            })
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат ID категории"
            )
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена"
            )
        
        # Проверяем соответствие типа транзакции и новой категории
        transaction_type = update_data.get("type", transaction["type"])
        if transaction_type != category["type"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Тип транзакции ({transaction_type}) не соответствует типу категории ({category['type']})"
            )
    
    # Обновляем время изменения
    update_data["updated_at"] = datetime.utcnow()
    
    await db.transactions.update_one(
        {"_id": ObjectId(transaction_id)},
        {"$set": update_data}
    )
    
    return await get_transaction_by_id(db, transaction_id, user_id)


async def delete_transaction(
    db: AsyncIOMotorDatabase, 
    transaction_id: str, 
    user_id: str
) -> bool:
    """
    Удаляет транзакцию
    """
    transaction = await get_transaction_by_id(db, transaction_id, user_id)
    
    if not transaction:
        return False
    
    result = await db.transactions.delete_one({"_id": ObjectId(transaction_id)})
    return result.deleted_count > 0


async def get_transaction_stats(
    db: AsyncIOMotorDatabase, 
    user_id: str,
    period: str = "month",
    currency: Optional[str] = None
) -> Dict[str, Any]:
    """
    Получает статистику по транзакциям в заданном периоде
    """
    now = datetime.utcnow()
    
    # Определяем период времени
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now - timedelta(days=30)  # По умолчанию 30 дней
    
    # Базовый запрос с учетом пользователя и периода
    base_match = {
        "user_id": user_id,
        "date": {"$gte": start_date}
    }
    
    if currency:
        base_match["currency"] = currency
    
    # Получаем суммы доходов и расходов
    income_match = {**base_match, "type": TransactionType.INCOME}
    expense_match = {**base_match, "type": TransactionType.EXPENSE}
    
    # Агрегация доходов по валютам
    income_pipeline = [
        {"$match": income_match},
        {"$group": {
            "_id": "$currency",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    # Агрегация расходов по валютам
    expense_pipeline = [
        {"$match": expense_match},
        {"$group": {
            "_id": "$currency",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    # Агрегация расходов по категориям
    expense_by_category_pipeline = [
        {"$match": expense_match},
        {"$lookup": {
            "from": "categories",
            "localField": "category_id",
            "foreignField": "_id",
            "as": "category"
        }},
        {"$unwind": "$category"},
        {"$group": {
            "_id": {
                "category_id": "$category_id",
                "currency": "$currency"
            },
            "category_name": {"$first": "$category.name"},
            "icon": {"$first": "$category.icon"},
            "color": {"$first": "$category.color"},
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total": -1}}
    ]
    
    # Агрегация доходов по категориям
    income_by_category_pipeline = [
        {"$match": income_match},
        {"$lookup": {
            "from": "categories",
            "localField": "category_id",
            "foreignField": "_id",
            "as": "category"
        }},
        {"$unwind": "$category"},
        {"$group": {
            "_id": {
                "category_id": "$category_id",
                "currency": "$currency"
            },
            "category_name": {"$first": "$category.name"},
            "icon": {"$first": "$category.icon"},
            "color": {"$first": "$category.color"},
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total": -1}}
    ]
    
    # Выполняем все агрегации параллельно
    income_results = await db.transactions.aggregate(income_pipeline).to_list(length=100)
    expense_results = await db.transactions.aggregate(expense_pipeline).to_list(length=100)
    expense_by_category = await db.transactions.aggregate(expense_by_category_pipeline).to_list(length=100)
    income_by_category = await db.transactions.aggregate(income_by_category_pipeline).to_list(length=100)
    
    # Форматируем результаты по категориям
    expense_categories = []
    income_categories = []
    
    for item in expense_by_category:
        expense_categories.append({
            "category_id": str(item["_id"]["category_id"]),
            "category_name": item["category_name"],
            "icon": item["icon"],
            "color": item["color"],
            "currency": item["_id"]["currency"],
            "total": item["total"],
            "count": item["count"]
        })
    
    for item in income_by_category:
        income_categories.append({
            "category_id": str(item["_id"]["category_id"]),
            "category_name": item["category_name"],
            "icon": item["icon"],
            "color": item["color"],
            "currency": item["_id"]["currency"],
            "total": item["total"],
            "count": item["count"]
        })
    
    # Формируем итоговый ответ
    return {
        "period": period,
        "start_date": start_date,
        "end_date": now,
        "income": {
            "by_currency": income_results,
            "total_count": sum(item["count"] for item in income_results),
            "by_category": income_categories
        },
        "expense": {
            "by_currency": expense_results,
            "total_count": sum(item["count"] for item in expense_results),
            "by_category": expense_categories
        }
    } 