import json
import os
from typing import List, Type, Optional

import redis.asyncio as asyncredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from dotenv import load_dotenv

from core.models.models import (Product, ProductionBatches,
                                WarehouseInventory, Shipment,
                                ShipmentItems)
from core.schemas.schemas import (ProductGet, ShipmentPost,
                                  ProductionBatchesPost,
                                  ProductionBatchesPatchStatus,
                                  WarehouseInventoryPut,
                                  ReceiveBatchInWarehouseGet,
                                  WarehouseInventoryGet, ShipmentEntity)
from core.models.db import get_db
from .endpoints import (production_batches, products,
                        warehouse)
from core.models.crud import (get_or_404, ModelType,
                              joined_production_batch_with_product,
                              generate_unique_order_id,
                              filter_batch_ids)
from api.constants_api import (PRODUCTION_BATCH_CREATION_ERROR,
                               ERROR_STATUS_RECEIVE_BATCH,
                               ERROR_BATCH_ID_RECEIVE_BATCH, CACHE_TIME)

load_dotenv()

redis = asyncredis.from_url(os.getenv('REDIS_URL'),
                            decode_responses=True)


def structure_response_for_batch(batch: Type[ModelType],
                                 product_model: Optional[str] = None):
    response_batch_content = {
        'id': batch.id,
        'product_id': batch.product_id,
        'start_date': batch.start_date.isoformat(),
        'current_stage': batch.current_stage,
        'quantity_to_be_produced': batch.quantity_in_batch
    }
    if product_model is not None:
        response_batch_content.update({'product_model': product_model})
    return response_batch_content


@products.get('/', response_model=List[ProductGet],
              status_code=status.HTTP_200_OK)
async def get_products(db: AsyncSession = Depends(get_db)):
    cache_key = 'all_products'
    cached_data = await redis.get(cache_key)

    if cached_data:
        return json.loads(cached_data)
    result = await db.execute(select(Product))
    all_products = result.scalars().all()

    serialized_data = [ProductGet.from_orm(product).model_dump()
                       for product in all_products]
    await redis.set(cache_key, json.dumps(serialized_data), ex=CACHE_TIME)

    return all_products


@products.get('/{product_id}', response_model=ProductGet,
              status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await get_or_404(db=db, model=Product,
                            identifier=product_id)


@production_batches.post('/', response_class=JSONResponse)
async def post_production_batch(
        production_batch: ProductionBatchesPost,
        db: AsyncSession = Depends(get_db)):
    product = await get_or_404(
        db=db, model=Product, uuid_identifier=production_batch.product_id)

    new_production_batch = ProductionBatches(
        product_id=product.id, **production_batch.model_dump(
            exclude={'product_id'}))
    db.add(new_production_batch)
    await db.commit()
    await db.refresh(new_production_batch)
    fetched_data = await joined_production_batch_with_product(
        db=db, model1=Product, model2=ProductionBatches,
        identifier=new_production_batch.id)

    if fetched_data:
        product_model, batch = fetched_data

        response_content = structure_response_for_batch(
            product_model=product_model, batch=batch)
        return JSONResponse(content=response_content,
                            status_code=status.HTTP_201_CREATED)
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
    updated_batch = structure_response_for_batch(batch=current_batch)
    updated_batch.update({'previous_stage': previous_stage})
    response_content = {
        'message': 'Stage updated successfully.',
        'updated_batch': updated_batch
    }
    return JSONResponse(content=response_content)


@warehouse.put('/receive-batch/{batch_id}', response_class=JSONResponse)
async def receive_batch_in_warehouse(
        batch_id: int, new_inventory_batch: WarehouseInventoryPut,
        db: AsyncSession = Depends(get_db)):
    success_message = {'message': 'Batch received successfully.'}
    batch = await get_or_404(db=db, model=ProductionBatches,
                             identifier=batch_id)
    if batch.current_stage != 'COMPLETED':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_STATUS_RECEIVE_BATCH)
    batch_inventory_query = await db.execute(
        select(WarehouseInventory).filter(
            WarehouseInventory.batch_id == batch_id)
    )
    batch_exists = batch_inventory_query.scalar_one_or_none()
    if batch_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_BATCH_ID_RECEIVE_BATCH
        )

    received_batch_in_warehouse = WarehouseInventory(
        product_id=batch.product_id, batch_id=batch_id,
        stock_quantity=new_inventory_batch.quantity_received,
        **new_inventory_batch.model_dump(exclude={'quantity_received'}))
    db.add(received_batch_in_warehouse)
    await db.commit()
    await db.refresh(received_batch_in_warehouse)
    created_batch = await db.get(
        WarehouseInventory, received_batch_in_warehouse.id)
    success_message.update({
        'received_batch': ReceiveBatchInWarehouseGet.from_orm(
            created_batch).model_dump()})
    return JSONResponse(
        content=success_message, status_code=status.HTTP_200_OK
    )


@warehouse.get('/inventory', response_class=JSONResponse)
async def get_all_inventory(db: AsyncSession = Depends(get_db)):
    cache_key = 'warehouse_inventory'
    cached_data = await redis.get(cache_key)

    if cached_data:
        return json.loads(cached_data)

    query_models = await db.execute(
        select(WarehouseInventory))
    results = query_models.scalars().all()

    inventory = [
        WarehouseInventoryGet.from_orm(row).model_dump(
            exclude={'id'}) for row in results
    ]
    inventory_dict = {'inventory': inventory}
    await redis.set(cache_key, json.dumps(inventory_dict), ex=CACHE_TIME)
    return JSONResponse(content=inventory_dict,
                        status_code=status.HTTP_200_OK)


@warehouse.post('/shipments', response_class=JSONResponse,
                status_code=status.HTTP_201_CREATED)
async def post_order(
        new_shipment: ShipmentPost,
        db: AsyncSession = Depends(get_db)):
    order_id = await generate_unique_order_id(db=db, model=Shipment)
    batch_ids = [order.batch_id for order in new_shipment.items]
    batches_checked = await filter_batch_ids(
        db=db, model=WarehouseInventory, batch_ids=batch_ids)
    await filter_batch_ids(db=db, model=ShipmentItems, batch_ids=batch_ids,
                           check_shipments=True)

    await db.execute(update(WarehouseInventory).where(
        WarehouseInventory.batch_id.in_(
            [inventory.batch_id for inventory in batches_checked])).values(
        in_shipment=True, stock_quantity=0
    ))

    shipment = Shipment(order_id=order_id, status=new_shipment.status)
    db.add(shipment)
    await db.flush()

    shipment_items = [ShipmentItems(
        shipment_id=shipment.id, batch_id=batch_id) for batch_id in batch_ids]
    db.add_all(shipment_items)

    await db.flush()
    await db.commit()
    await db.refresh(shipment)
    response_data = {
        'shipment_id': shipment.id,
        'order_id': shipment.order_id,
        'items': [{'batch_id': batch} for batch in batch_ids],
        'status': shipment.status
    }
    return response_data


@warehouse.patch('/change-status', response_class=JSONResponse)
async def change_shipment_status(
        shipment_id: int, new_status_shipment: ShipmentEntity,
        db: AsyncSession = Depends(get_db)):
    success_message = {'status': 'status has been changed'}
    shipment = await get_or_404(db=db, model=Shipment, identifier=shipment_id)
    shipment.status = new_status_shipment.status
    await db.commit()

    return JSONResponse(content=success_message,
                        status_code=status.HTTP_200_OK)
