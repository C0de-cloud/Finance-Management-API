from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status

from app.core.security import verify_password, get_password_hash
from app.models.user import UserCreate, UserUpdate, UserRole, Currency


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[Dict[str, Any]]:
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        
        user["id"] = str(user["_id"])
        del user["_id"]
        
        if "password" in user:
            del user["password"]
        
        return user
    except Exception:
        return None


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[Dict[str, Any]]:
    user = await db.users.find_one({"email": email})
    if not user:
        return None
    
    user["id"] = str(user["_id"])
    del user["_id"]
    
    return user


async def get_user_by_username(db: AsyncIOMotorDatabase, username: str) -> Optional[Dict[str, Any]]:
    user = await db.users.find_one({"username": username})
    if not user:
        return None
    
    user["id"] = str(user["_id"])
    del user["_id"]
    
    return user


async def create_user(db: AsyncIOMotorDatabase, user_data: UserCreate) -> Dict[str, Any]:
    if await get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if await get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    user_dict = user_data.model_dump()
    now = datetime.utcnow()
    
    hashed_password = get_password_hash(user_dict["password"])
    user_dict["password"] = hashed_password
    user_dict["role"] = UserRole.USER
    user_dict["created_at"] = now
    user_dict["updated_at"] = now
    
    result = await db.users.insert_one(user_dict)
    
    # Создаем базовые категории для пользователя
    await create_default_categories(db, str(result.inserted_id))
    
    created_user = await get_user_by_id(db, str(result.inserted_id))
    return created_user


async def update_user(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    user_data: UserUpdate
) -> Optional[Dict[str, Any]]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    update_data = {k: v for k, v in user_data.model_dump(exclude_unset=True).items() if v is not None}
    
    if "email" in update_data and update_data["email"] != user["email"]:
        if await get_user_by_email(db, update_data["email"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    if "username" in update_data and update_data["username"] != user["username"]:
        if await get_user_by_username(db, update_data["username"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    
    return await get_user_by_id(db, user_id)


async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    try:
        result = await db.users.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count:
            # Удаляем связанные данные
            await db.transactions.delete_many({"user_id": user_id})
            await db.categories.delete_many({"user_id": user_id})
            await db.budgets.delete_many({"user_id": user_id})
            await db.goals.delete_many({"user_id": user_id})
            return True
        return False
    except Exception:
        return False


async def authenticate_user(
    db: AsyncIOMotorDatabase, 
    username_or_email: str, 
    password: str
) -> Optional[Dict[str, Any]]:
    user = await get_user_by_username(db, username_or_email)
    
    if not user:
        user = await get_user_by_email(db, username_or_email)
    
    if not user:
        return None
    
    user_with_password = await db.users.find_one({"_id": ObjectId(user["id"])})
    
    if not verify_password(password, user_with_password["password"]):
        return None
    
    return user


async def change_user_password(
    db: AsyncIOMotorDatabase,
    user_id: str,
    current_password: str,
    new_password: str
) -> bool:
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return False
    
    if not verify_password(current_password, user["password"]):
        return False
    
    hashed_password = get_password_hash(new_password)
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed_password, "updated_at": datetime.utcnow()}}
    )
    
    return True


async def create_default_categories(db: AsyncIOMotorDatabase, user_id: str) -> None:
    from app.models.transaction import TransactionType
    
    default_categories = [
        # Доходы
        {"name": "Зарплата", "type": TransactionType.INCOME, "icon": "cash", "color": "#4CAF50"},
        {"name": "Бонусы", "type": TransactionType.INCOME, "icon": "gift", "color": "#8BC34A"},
        {"name": "Депозиты", "type": TransactionType.INCOME, "icon": "bank", "color": "#009688"},
        {"name": "Инвестиции", "type": TransactionType.INCOME, "icon": "chart-line", "color": "#03A9F4"},
        {"name": "Прочие доходы", "type": TransactionType.INCOME, "icon": "plus-circle", "color": "#2196F3"},
        
        # Расходы
        {"name": "Продукты", "type": TransactionType.EXPENSE, "icon": "cart-shopping", "color": "#FF9800"},
        {"name": "Рестораны", "type": TransactionType.EXPENSE, "icon": "utensils", "color": "#F44336"},
        {"name": "Транспорт", "type": TransactionType.EXPENSE, "icon": "car", "color": "#3F51B5"},
        {"name": "ЖКХ", "type": TransactionType.EXPENSE, "icon": "house", "color": "#673AB7"},
        {"name": "Связь", "type": TransactionType.EXPENSE, "icon": "mobile", "color": "#9C27B0"},
        {"name": "Развлечения", "type": TransactionType.EXPENSE, "icon": "film", "color": "#E91E63"},
        {"name": "Здоровье", "type": TransactionType.EXPENSE, "icon": "heart-pulse", "color": "#F06292"},
        {"name": "Одежда", "type": TransactionType.EXPENSE, "icon": "shirt", "color": "#FF5722"},
        {"name": "Образование", "type": TransactionType.EXPENSE, "icon": "book", "color": "#795548"},
        {"name": "Прочие расходы", "type": TransactionType.EXPENSE, "icon": "minus-circle", "color": "#607D8B"}
    ]
    
    now = datetime.utcnow()
    for category in default_categories:
        category["user_id"] = user_id
        category["is_default"] = True
        category["created_at"] = now
        category["updated_at"] = now
    
    if default_categories:
        await db.categories.insert_many(default_categories)


async def get_user_statistics(db: AsyncIOMotorDatabase, user_id: str, currency: Currency) -> Dict[str, Any]:
    from app.models.transaction import TransactionType
    
    # Получаем общую сумму доходов
    total_income_pipeline = [
        {"$match": {"user_id": user_id, "type": TransactionType.INCOME, "currency": currency}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    total_income_result = await db.transactions.aggregate(total_income_pipeline).to_list(length=1)
    total_income = total_income_result[0]["total"] if total_income_result else 0
    
    # Получаем общую сумму расходов
    total_expense_pipeline = [
        {"$match": {"user_id": user_id, "type": TransactionType.EXPENSE, "currency": currency}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    total_expense_result = await db.transactions.aggregate(total_expense_pipeline).to_list(length=1)
    total_expense = total_expense_result[0]["total"] if total_expense_result else 0
    
    # Расчет баланса
    balance = total_income - total_expense
    
    # Получаем доходы за текущий месяц
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    
    month_income_pipeline = [
        {
            "$match": {
                "user_id": user_id, 
                "type": TransactionType.INCOME, 
                "currency": currency,
                "date": {"$gte": current_month, "$lt": next_month}
            }
        },
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    month_income_result = await db.transactions.aggregate(month_income_pipeline).to_list(length=1)
    month_income = month_income_result[0]["total"] if month_income_result else 0
    
    # Получаем расходы за текущий месяц
    month_expense_pipeline = [
        {
            "$match": {
                "user_id": user_id, 
                "type": TransactionType.EXPENSE, 
                "currency": currency,
                "date": {"$gte": current_month, "$lt": next_month}
            }
        },
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    month_expense_result = await db.transactions.aggregate(month_expense_pipeline).to_list(length=1)
    month_expense = month_expense_result[0]["total"] if month_expense_result else 0
    
    month_balance = month_income - month_expense
    
    # Получаем топ-5 категорий расходов
    top_expense_categories_pipeline = [
        {
            "$match": {
                "user_id": user_id, 
                "type": TransactionType.EXPENSE, 
                "currency": currency
            }
        },
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
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
    top_expense_categories = await db.transactions.aggregate(top_expense_categories_pipeline).to_list(length=5)
    
    # Получаем топ-5 категорий доходов
    top_income_categories_pipeline = [
        {
            "$match": {
                "user_id": user_id, 
                "type": TransactionType.INCOME, 
                "currency": currency
            }
        },
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
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
    top_income_categories = await db.transactions.aggregate(top_income_categories_pipeline).to_list(length=5)
    
    # Получаем последние 10 транзакций
    recent_transactions_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"date": -1}},
        {"$limit": 10},
        {
            "$lookup": {
                "from": "categories",
                "localField": "category_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
        {"$unwind": "$category"},
        {
            "$project": {
                "_id": 1,
                "type": 1,
                "amount": 1,
                "currency": 1,
                "description": 1,
                "date": 1,
                "category_name": "$category.name",
                "category_icon": "$category.icon",
                "category_color": "$category.color"
            }
        }
    ]
    recent_transactions = await db.transactions.aggregate(recent_transactions_pipeline).to_list(length=10)
    
    # Форматируем ID для JSON
    for transaction in recent_transactions:
        transaction["id"] = str(transaction["_id"])
        del transaction["_id"]
        
    for category in top_expense_categories:
        category["id"] = str(category["_id"])
        del category["_id"]
        
    for category in top_income_categories:
        category["id"] = str(category["_id"])
        del category["_id"]
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "currency": currency,
        "month_income": month_income,
        "month_expense": month_expense,
        "month_balance": month_balance,
        "top_expense_categories": top_expense_categories,
        "top_income_categories": top_income_categories,
        "recent_transactions": recent_transactions
    } 