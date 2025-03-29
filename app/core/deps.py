from typing import Annotated, Dict, Optional
from jose import JWTError, jwt
from datetime import datetime, date

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.db.mongodb import get_database
from app.models.user import UserRole
from app.models.transaction import TransactionType
from app.crud.user import get_user_by_id

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> Dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_admin_user(
    current_user: Annotated[Dict, Depends(get_current_user)]
) -> Dict:
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


async def pagination_params(
    limit: Annotated[int, Query(10, ge=1, le=100)],
    offset: Annotated[int, Query(0, ge=0)]
) -> Dict:
    return {"limit": limit, "offset": offset}


async def transaction_filter_params(
    transaction_type: Annotated[Optional[TransactionType], Query(None)],
    category_id: Annotated[Optional[str], Query(None)],
    min_amount: Annotated[Optional[float], Query(None)],
    max_amount: Annotated[Optional[float], Query(None)],
    start_date: Annotated[Optional[date], Query(None)],
    end_date: Annotated[Optional[date], Query(None)],
    tag: Annotated[Optional[str], Query(None)],
    search: Annotated[Optional[str], Query(None)]
) -> Dict:
    filters = {}
    if transaction_type:
        filters["type"] = transaction_type
    if category_id:
        filters["category_id"] = category_id
    
    if min_amount is not None or max_amount is not None:
        filters["amount"] = {}
        if min_amount is not None:
            filters["amount"]["$gte"] = min_amount
        if max_amount is not None:
            filters["amount"]["$lte"] = max_amount
    
    if start_date is not None or end_date is not None:
        filters["date"] = {}
        if start_date is not None:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            filters["date"]["$gte"] = start_datetime
        if end_date is not None:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            filters["date"]["$lte"] = end_datetime
    
    if tag:
        filters["tags"] = tag
    
    if search:
        filters["$text"] = {"$search": search}
    
    return filters


async def budget_filter_params(
    is_active: Annotated[Optional[bool], Query(None)],
    category_id: Annotated[Optional[str], Query(None)],
    search: Annotated[Optional[str], Query(None)]
) -> Dict:
    filters = {}
    
    if is_active is not None:
        now = datetime.now().date()
        if is_active:
            filters["$and"] = [
                {"start_date": {"$lte": now}},
                {"end_date": {"$gte": now}}
            ]
        else:
            filters["$or"] = [
                {"start_date": {"$gt": now}},
                {"end_date": {"$lt": now}}
            ]
    
    if category_id:
        filters["category_id"] = category_id
    
    if search:
        filters["$text"] = {"$search": search}
    
    return filters


async def goal_filter_params(
    is_completed: Annotated[Optional[bool], Query(None)],
    search: Annotated[Optional[str], Query(None)]
) -> Dict:
    filters = {}
    
    if is_completed is not None:
        filters["is_completed"] = is_completed
    
    if search:
        filters["$text"] = {"$search": search}
    
    return filters 