from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated

from app.db.mongodb import get_database
from app.core.deps import get_current_user, get_current_admin_user
from app.crud.user import get_user_by_id, update_user, delete_user, get_user_statistics
from app.models.user import User, UserUpdate, UserWithStats, Currency

router = APIRouter()


@router.get("/me", response_model=User)
async def read_user_me(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Получение информации о текущем пользователе
    """
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
    user_data: UserUpdate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Обновление данных текущего пользователя
    """
    updated_user = await update_user(db, current_user["id"], user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return updated_user


@router.get("/me/statistics", response_model=UserWithStats)
async def get_current_user_statistics(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[dict, Depends(get_current_user)],
    currency: Currency = Currency.RUB
):
    """
    Получение финансовой статистики текущего пользователя
    """
    stats = await get_user_statistics(db, current_user["id"], currency)
    return {**current_user, **stats}


@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    _: Annotated[dict, Depends(get_current_admin_user)]  # Только для админов
):
    """
    Получение информации о пользователе по ID (только для админов)
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user_by_id(
    user_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    _: Annotated[dict, Depends(get_current_admin_user)]  # Только для админов
):
    """
    Удаление пользователя по ID (только для админов)
    """
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return 