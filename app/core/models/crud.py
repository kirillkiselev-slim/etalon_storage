from typing import Type, TypeVar, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from starlette import status

from app.core.models.models import Base


ModelType = TypeVar('ModelType', bound=Base)
ItemType = TypeVar('ItemType', bound=BaseModel)


async def get_or_404(
        db: AsyncSession,
        model: Type[ModelType],
        identifier: Optional[int] = None,
        join_load: Optional[bool] = None,
) -> ModelType:
    """
    Функция, которая возвращает объект по ИД. Если select_load=True,
    то выполняется запрос для выборки полей product_id и amount_of_product.
    """
    exception = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'{model.__name__} с ИД {identifier} не найден.'
            )
    if not join_load and identifier:
        obj = await db.get(model, identifier)
        if not obj:
            raise exception
        return obj

    elif join_load and identifier:
        query = await db.execute(
            select(model).options(
                joinedload(model.order_items)).where(model.id == identifier)
        )
        order = query.scalars().first()

        if not order:
            raise exception
        products = {item.product_id: item.amount_of_product
                    for item in order.order_items}
        return {
            'id': order.id,
            'created_at': order.created_at,
            'status': order.status,
            'products': products
        }
