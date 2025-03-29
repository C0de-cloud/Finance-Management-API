from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.category import CategoryCreate, CategoryUpdate


async def get_categories(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Получает список категорий пользователя
    """
    categories = await db.categories.find(
        {"user_id": user_id}
    ).skip(skip).limit(limit).to_list(length=limit)
    
    # Преобразуем ObjectId в строку для JSON сериализации
    for category in categories:
        category["id"] = str(category["_id"])
        del category["_id"]
    
    return categories


async def get_category_by_id(
    db: AsyncIOMotorDatabase, 
    category_id: str, 
    user_id: str
) -> Optional[Dict[str, Any]]:
    """
    Получает категорию по ID
    """
    try:
        category = await db.categories.find_one(
            {"_id": ObjectId(category_id), "user_id": user_id}
        )
    except:
        return None
    
    if category:
        category["id"] = str(category["_id"])
        del category["_id"]
        return category
    
    return None


async def create_category(
    db: AsyncIOMotorDatabase, 
    category_data: CategoryCreate, 
    user_id: str
) -> Dict[str, Any]:
    """
    Создает новую категорию
    """
    # Проверяем существование категории с таким же именем у пользователя
    existing = await db.categories.find_one({
        "name": category_data.name, 
        "type": category_data.type,
        "user_id": user_id
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Категория с именем '{category_data.name}' для типа '{category_data.type}' уже существует"
        )
    
    category_dict = category_data.model_dump()
    now = datetime.utcnow()
    
    category_dict["user_id"] = user_id
    category_dict["is_default"] = False
    category_dict["created_at"] = now
    category_dict["updated_at"] = now
    
    result = await db.categories.insert_one(category_dict)
    
    new_category = await get_category_by_id(db, str(result.inserted_id), user_id)
    return new_category


async def update_category(
    db: AsyncIOMotorDatabase, 
    category_id: str, 
    category_data: CategoryUpdate, 
    user_id: str
) -> Optional[Dict[str, Any]]:
    """
    Обновляет существующую категорию
    """
    category = await get_category_by_id(db, category_id, user_id)
    
    if not category:
        return None
    
    # Проверяем, является ли категория системной
    if category.get("is_default", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно изменить системную категорию"
        )
    
    # Если имя меняется, проверяем его уникальность
    update_data = {k: v for k, v in category_data.model_dump(exclude_unset=True).items() if v is not None}
    
    if "name" in update_data and update_data["name"] != category["name"]:
        existing = await db.categories.find_one({
            "name": update_data["name"],
            "type": category["type"],
            "user_id": user_id,
            "_id": {"$ne": ObjectId(category_id)}
        })
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Категория с именем '{update_data['name']}' для типа '{category['type']}' уже существует"
            )
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.categories.update_one(
        {"_id": ObjectId(category_id)},
        {"$set": update_data}
    )
    
    return await get_category_by_id(db, category_id, user_id)


async def delete_category(
    db: AsyncIOMotorDatabase, 
    category_id: str, 
    user_id: str
) -> bool:
    """
    Удаляет категорию, если она не является системной
    """
    category = await get_category_by_id(db, category_id, user_id)
    
    if not category:
        return False
    
    # Запрещаем удалять системные категории
    if category.get("is_default", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно удалить системную категорию"
        )
    
    # Проверяем, есть ли транзакции с этой категорией
    transactions_count = await db.transactions.count_documents({"category_id": category_id})
    
    if transactions_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Невозможно удалить категорию, так как с ней связано {transactions_count} транзакций"
        )
    
    result = await db.categories.delete_one({"_id": ObjectId(category_id)})
    return result.deleted_count > 0


async def get_category_with_stats(
    db: AsyncIOMotorDatabase, 
    category_id: str, 
    user_id: str,
    time_period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Получает информацию о категории вместе со статистикой использования
    """
    category = await get_category_by_id(db, category_id, user_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Формируем условие для временного периода
    date_match = {}
    now = datetime.utcnow()
    
    if time_period == "week":
        start_date = now - timedelta(days=7)
        date_match = {"date": {"$gte": start_date}}
    elif time_period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_match = {"date": {"$gte": start_date}}
    elif time_period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        date_match = {"date": {"$gte": start_date}}
    
    # Получаем статистику транзакций
    match_condition = {
        "category_id": category_id,
        "user_id": user_id,
        **date_match
    }
    
    pipeline = [
        {"$match": match_condition},
        {"$group": {
            "_id": "$currency",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1},
            "avg": {"$avg": "$amount"}
        }},
        {"$sort": {"total": -1}}
    ]
    
    stats_by_currency = await db.transactions.aggregate(pipeline).to_list(length=10)
    
    # Получаем недавние транзакции
    recent_transactions = await db.transactions.find(
        match_condition
    ).sort([("date", -1)]).limit(5).to_list(length=5)
    
    # Форматируем ID для JSON
    for transaction in recent_transactions:
        transaction["id"] = str(transaction["_id"])
        del transaction["_id"]
    
    return {
        **category,
        "stats": {
            "by_currency": stats_by_currency,
            "total_transactions": sum(stat["count"] for stat in stats_by_currency),
        },
        "recent_transactions": recent_transactions
    } 