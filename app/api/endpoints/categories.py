from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated, List, Optional

from app.db.mongodb import get_database
from app.core.deps import get_current_user, pagination_params
from app.crud.category import (
    get_categories, 
    get_category_by_id, 
    create_category, 
    update_category, 
    delete_category,
    get_category_with_stats
)
from app.models.category import Category, CategoryCreate, CategoryUpdate, CategoryWithStats, CategoryList
from app.models.transaction import TransactionType

router = APIRouter()


@router.get("", response_model=List[Category])
async def read_categories(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)],
    type: Optional[TransactionType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Получение списка категорий текущего пользователя
    """
    categories = await get_categories(db, current_user["id"], skip, limit)
    
    # Фильтрация по типу если указан
    if type:
        categories = [c for c in categories if c["type"] == type]
        
    return categories


@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_new_category(
    category_data: CategoryCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Создание новой категории
    """
    return await create_category(db, category_data, current_user["id"])


@router.get("/{category_id}", response_model=Category)
async def read_category(
    category_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Получение информации о категории по ID
    """
    category = await get_category_by_id(db, category_id, current_user["id"])
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    return category


@router.get("/{category_id}/stats", response_model=CategoryWithStats)
async def read_category_with_stats(
    category_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)],
    period: Optional[str] = Query(None, description="Период статистики (week, month, year)")
):
    """
    Получение информации о категории вместе со статистикой использования
    """
    return await get_category_with_stats(db, category_id, current_user["id"], period)


@router.put("/{category_id}", response_model=Category)
async def update_category_by_id(
    category_id: str,
    category_data: CategoryUpdate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Обновление категории
    """
    updated_category = await update_category(db, category_id, category_data, current_user["id"])
    if not updated_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    return updated_category


@router.delete("/{category_id}", status_code=204)
async def delete_category_by_id(
    category_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Удаление категории
    """
    await delete_category(db, category_id, current_user["id"])
    return 