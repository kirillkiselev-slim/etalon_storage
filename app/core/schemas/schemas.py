import datetime
import uuid
from typing import Annotated

from pydantic import BaseModel, fields, ConfigDict, field_validator
from core.constants import (PRODUCTION_BATCHES_REGEX,
                                PRODUCTION_BATCHES_DESCRIPTION_STATUS,
                                PRODUCT_DESCRIPTION_STATUS, PRODUCT_REGEX,
                                SHIPMENTS_REGEX, SHIPMENTS_DESCRIPTION_STATUS, )


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProductGet(BaseConfigModel):
    id: int
    product_uuid: str
    name: str
    name_model: str
    status: str


class WarehouseInventoryPut(BaseConfigModel):
    storage_location: Annotated[str, fields.Field(
        min_length=2, max_length=55)]
    quantity_received: Annotated[int, fields.Field(ge=0)]


class ReceiveBatchInWarehouseGet(BaseConfigModel):
    id: int
    product_id: int
    storage_location: str
    stock_quantity: int


class WarehouseInventoryGet(BaseConfigModel):
    product_id: int
    stock_quantity: int
    storage_location: str


class ProductionBatchesPost(BaseConfigModel):
    product_id: str
    start_date: datetime.datetime = fields.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        validate_default=True)
    quantity_in_batch: Annotated[int, fields.Field(ge=1)]

    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, date: datetime.datetime) -> datetime.datetime:
        if date > datetime.datetime.now(datetime.UTC):
            raise ValueError('"Start date" cannot be in the future!')
        return date


class ProductionBatchesPatchStatus(BaseConfigModel):
    new_stage: Annotated[str, fields.Field(
        pattern=PRODUCTION_BATCHES_REGEX, default='PRODUCTION_STARTED',
        description=PRODUCTION_BATCHES_DESCRIPTION_STATUS)]


class ItemBatchesSchema(BaseConfigModel):
    batch_id: int = fields.Field(gt=0)


class ShipmentEntity(BaseConfigModel):
    status: str = fields.Field(
        min_length=5, default='PENDING',
        pattern=SHIPMENTS_REGEX,
        description=SHIPMENTS_DESCRIPTION_STATUS)


class ShipmentPost(ShipmentEntity):
    items: list[ItemBatchesSchema]


