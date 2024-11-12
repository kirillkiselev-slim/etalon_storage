import string
import random
from typing import Type, TypeVar, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from starlette import status

from app.core.models.models import Base
from app.core.constants import PRODUCT_EXISTS

ModelType = TypeVar('ModelType', bound=Base)
ItemType = TypeVar('ItemType', bound=BaseModel)


async def get_or_404(
        db: AsyncSession,
        model: Type[ModelType],
        identifier: Optional[int] = None,
        uuid_identifier: Optional[str] = None
) -> ModelType:
    """
    Функция, которая возвращает объект по ИД. Если select_load=True,
    то выполняется запрос для выборки полей product_id и amount_of_product.
    """
    exception = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'{model.__name__} with ID {identifier} is not found'
            )
    if identifier and uuid_identifier is None:
        obj = await db.get(model, identifier)
        if obj:
            return obj
        raise exception
    else:
        obj = await db.execute(select(model).filter(
            model.product_uuid == uuid_identifier))
        fetched_obj = obj.scalar()
        if fetched_obj:
            return fetched_obj
        raise exception


async def generate_unique_order_id(
        db: AsyncSession, model: Type[ModelType]) -> str:
    while True:
        order_id = 'ORD' + ''.join(random.choice(string.digits)
                                   for _ in range(6))
        result = await db.execute(select(model).filter_by(order_id=order_id))
        existing_order = result.scalar()
        if not existing_order:
            return order_id


async def joined_production_batch_with_product(
        db: AsyncSession,
        model1: Type[ModelType],
        model2: Type[ModelType],
        identifier: Optional[int] = None,
) -> ModelType:
    result = await db.execute(
        select(model1.model_name, model2)
        .join(model1, model1.id == model2.id)
        .filter(model2.id == identifier)
    )
    fetched_data = result.first()
    return fetched_data


async def filter_batch_id_in_warehouse(
        db: AsyncSession,
        model: Type[ModelType],
        batch_id: int):
    """
    Функция, которая проверяет наличие такого же имени продукта.
    """
    result = await db.execute(
        select(model).filter(model.batch_id == batch_id))

    product_in_db = result.scalars().first()
    if product_in_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=PRODUCT_EXISTS)
