import datetime
from decimal import Decimal
from typing import Dict, Annotated

from pydantic import BaseModel, fields, conint, ConfigDict, field_validator
from app.core.constants import (PRODUCTION_BATCHES_REGEX,
                                PRODUCTION_BATCHES_DESCRIPTION_STATUS,
                                PRODUCT_DESCRIPTION_STATUS, PRODUCT_REGEX,
                                SHIPMENTS_REGEX, SHIPMENTS_DESCRIPTION_STATUS)


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProductGet(BaseConfigModel):
    id: int
    model_name: str
    status: str


class ProductCreate(BaseConfigModel):
    model_name: str = fields.Field(max_length=255, min_length=3)
    status: str = fields.Field(min_length=5, default='IN_STOCK',
                               pattern=PRODUCT_REGEX,
                               description=PRODUCT_DESCRIPTION_STATUS)


class WarehouseInventoryPut(BaseConfigModel):
    storage_location: Annotated[str, fields.Field(
        min_length=2, max_length=55)]


class WarehouseInventoryGet(BaseConfigModel):
    id: int
    product_id: int
    storage_location: str


class ProductionBatchesPost(BaseConfigModel):
    product_id: Annotated[int, fields.Field(ge=1)]
    start_date: datetime.datetime = fields.Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        validate_default=True)

    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, date: datetime.datetime) -> datetime.datetime:
        if date > datetime.datetime.now(datetime.UTC):
            raise ValueError('"Start date" не может быть в будущем!')
        return date


class ProductionBatchesGet(BaseConfigModel):
    id: int
    product_id: int
    model_name: str


class ProductionBatchesPatchStatus(BaseConfigModel):
    new_stage: Annotated[str, fields.Field(
        pattern=PRODUCTION_BATCHES_REGEX,
        description=PRODUCTION_BATCHES_DESCRIPTION_STATUS)]


class Shipment(BaseConfigModel):
    ...
