from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from pydantic import ValidationError

from app.core.models.models import (Product, ProductionBatches,
                                    WarehouseInventory, Shipment, ShipmentItems)
from app.core.schemas.schemas import Product
from app.core.models.db import get_db
from .endpoints import (production_batches, products,
                        warehouse, healthcheck)
from app.core.models.crud import get_or_404


@products.get('/', response_model=List[Product],
              status_code=status.HTTP_200_OK)
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    return result.scalars().all()


@products.get('/{product_id}', response_model=Product,
              status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await get_or_404(db=db, model=Product,
                            identifier=product_id)

@products.post('/', response_model=Product,
               status_code=status.HTTP_201_CREATED)
def post_product(db: AsyncSession = Depends(get_db)):
    ...


@products.delete('/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_or_404(db=db, model=Product, identifier=product_id)
    await db.delete(product)
    await db.commit()



@production_batches.post('/', response_model=...,
                         status_code=status.HTTP_201_CREATED)
def post_production_batch(db: AsyncSession = Depends(get_db)):
    ...


@production_batches.patch('/{batch_id}/stages', response_model=...,
                          status_code=status.HTTP_200_OK)
def modify_production_batch_status(batch_id: int,
                                   db: AsyncSession = Depends(get_db)):
    ...


@warehouse.put('/receive-batch/{batch_id}', response_model=...,
               status_code=status.HTTP_200_OK)
def receive_batch_in_warehouse(batch_id: int,
                               db: AsyncSession = Depends(get_db)):
    ...


@warehouse.get('/inventory', response_model=...,
               status_code=status.HTTP_200_OK)
def get_all_inventory(db: AsyncSession = Depends(get_db)):
    ...