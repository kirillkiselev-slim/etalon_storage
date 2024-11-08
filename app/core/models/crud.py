from typing import Type, TypeVar, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
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
) -> ModelType:
    """
    Функция, которая возвращает объект по ИД. Если select_load=True,
    то выполняется запрос для выборки полей product_id и amount_of_product.
    """
    exception = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'{model.__name__} с ИД {identifier} не найден.'
            )
    if identifier:
        obj = await db.get(model, identifier)
        if not obj:
            raise exception
        return obj

    # elif join_load and identifier:
    #     query = await db.execute(
    #         select(model).options(
    #             joinedload(model.order_items)).where(model.id == identifier)
    #     )
    #     order = query.scalars().first()
    #
    #     if not order:
    #         raise exception
    #     products = {item.product_id: item.amount_of_product
    #                 for item in order.order_items}
    #     return {
    #         'id': order.id,
    #         'created_at': order.created_at,
    #         'status': order.status,
    #         'products': products
    #     }


async def joined_production_batch_with_product(
        db: AsyncSession,
        model1: Type[ModelType],
        model2: Type[ModelType],
        identifier: Optional[int] = None,
) -> ModelType:
    result = await db.execute(
        select(model1.model_name, model2)
        .join(model1, model1.id == model2.product_id)
        .filter(model2.id == identifier)
    )
    fetched_data = result.first()
    return fetched_data


async def filter_model_name(
        db: AsyncSession,
        model: Type[ModelType],
        item: ItemType):
    """
    Функция, которая проверяет наличие такого же имени продукта.
    """
    result = await db.execute(
        select(model).filter(model.model_name == item.model_name))

    product_in_db = result.scalars().first()
    if product_in_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=PRODUCT_EXISTS)
