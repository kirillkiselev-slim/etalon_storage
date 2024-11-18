import string
import random
from typing import Type, TypeVar, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from starlette import status

from core.models.models import Base
from core.constants import BATCH_DOES_NOT_EXIST, BATCH_EXISTS_IN_SHIPMENTS

ModelType = TypeVar('ModelType', bound=Base)
ItemType = TypeVar('ItemType', bound=BaseModel)


async def get_or_404(
        db: AsyncSession,
        model: Type[ModelType],
        identifier: Optional[int] = None,
        uuid_identifier: Optional[str] = None
) -> ModelType:
    """Получает объект по ID или UUID, возвращает 404, если объект не найден."""
    identifier_info = identifier if identifier else uuid_identifier
    exception = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'{model.__name__} with ID '
                       f'{identifier_info} is not found'
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
    """Генерирует уникальный идентификатор заказа."""
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
    """Возвращает данные о производственной партии с информацией о продукте."""
    result = await db.execute(
        select(model1.name_model, model2)
        .join(model1, model1.id == model2.id)
        .filter(model2.id == identifier)
    )
    fetched_data = result.first()
    return fetched_data


async def filter_batch_ids(
        db: AsyncSession,
        model: Type[ModelType],
        batch_ids: list,
        check_shipments: bool = False):
    """Фильтрует идентификаторы партий и проверяет их наличие."""
    result = await db.execute(select(model).filter(
        model.batch_id.in_(batch_ids)))

    result_batches = result.scalars().all()
    if len(result_batches) != len(batch_ids) and not check_shipments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=BATCH_DOES_NOT_EXIST)
    elif result_batches and check_shipments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=BATCH_EXISTS_IN_SHIPMENTS)
    return result_batches


