from typing import List, Type, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from pydantic import ValidationError

from app.core.models.models import (Product, ProductionBatches,
                                    WarehouseInventory, Shipment,
                                    ShipmentItems)
from app.core.schemas.schemas import (ProductGet, ProductCreate,
                                      ProductionBatchesPost,
                                      ProductionBatchesPatchStatus)
from app.core.models.db import get_db
from .endpoints import (production_batches, products,
                        warehouse, healthcheck)
from app.core.models.crud import (get_or_404, filter_model_name, ModelType,
                                  joined_production_batch_with_product)
from app.api.constants_api import PRODUCTION_BATCH_CREATION_ERROR


def structure_response_for_batch(
        product_model: Union[str, None], batch: Type[ModelType]):
    response_batch_content = {
        'id': batch.id,
        'product_id': batch.product_id,
        'start_date': batch.start_date.isoformat(),
        'current_stage': batch.current_stage
    }
    if product_model is not None:
        response_batch_content.update({'product_model': product_model})
    return response_batch_content


@products.get('/', response_model=List[ProductGet],
              status_code=status.HTTP_200_OK)
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    return result.scalars().all()


@products.get('/{product_id}', response_model=ProductGet,
              status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await get_or_404(db=db, model=Product,
                            identifier=product_id)


@products.post('/', response_class=JSONResponse,
               status_code=status.HTTP_201_CREATED)
async def post_product(new_product: ProductCreate,
                       db: AsyncSession = Depends(get_db)):
    await filter_model_name(db=db, model=Product, item=new_product)
    new_product = Product(**new_product.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return JSONResponse(content={'success': 'model name saved!'})


@products.delete('/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_or_404(db=db, model=Product, identifier=product_id)
    await db.delete(product)
    await db.commit()


@production_batches.post('/', response_class=JSONResponse,
                         status_code=status.HTTP_201_CREATED)
async def post_production_batch(
        production_batch: ProductionBatchesPost,
        db: AsyncSession = Depends(get_db)):
    await get_or_404(db=db, model=Product,
                     identifier=production_batch.product_id)

    new_production_batch = ProductionBatches(**production_batch.model_dump())
    db.add(new_production_batch)
    await db.commit()
    await db.refresh(new_production_batch)
    fetched_data = await joined_production_batch_with_product(
        db=db, model1=Product, model2=ProductionBatches,
        identifier=new_production_batch.id)

    if fetched_data:
        product_model, batch = fetched_data

        response_content = structure_response_for_batch(product_model, batch)
        return JSONResponse(content=response_content)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=PRODUCTION_BATCH_CREATION_ERROR)


@production_batches.patch('/{batch_id}/stages', response_class=JSONResponse,
                          status_code=status.HTTP_200_OK)
async def modify_production_batch_status(
        new_stage: ProductionBatchesPatchStatus,
        batch_id: int, db: AsyncSession = Depends(get_db),
):
    current_batch = await get_or_404(
        db=db, model=ProductionBatches, identifier=batch_id)
    previous_stage = current_batch.current_stage
    current_batch.current_stage = new_stage.new_stage
    await db.commit()
    await db.refresh(current_batch)
    updated_batch = structure_response_for_batch(
        product_model=None, batch=current_batch)
    updated_batch.update({'previous_stage': previous_stage})
    response_content = {
        'message': 'Stage updated successfully.',
        'updated_batch': updated_batch
    }
    return JSONResponse(content=response_content)

#
# @warehouse.put('/receive-batch/{batch_id}', response_model=...,
#                status_code=status.HTTP_200_OK)
# async def receive_batch_in_warehouse(batch_id: int,
#                                db: AsyncSession = Depends(get_db)):
#     ...
#
#
# @warehouse.get('/inventory', response_model=...,
#                status_code=status.HTTP_200_OK)
# async def get_all_inventory(db: AsyncSession = Depends(get_db)):
#     ...
