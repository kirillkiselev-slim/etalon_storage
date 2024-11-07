import datetime
from decimal import Decimal
from typing import Dict, Annotated

from pydantic import BaseModel, fields, conint, ConfigDict
from app.core.constants import (PRODUCTION_BATCHES_REGEX,
                                PRODUCTION_BATCHES_DESCRIPTION_STATUS,
                                PRODUCT_DESCRIPTION_STATUS, PRODUCT_REGEX,
                                SHIPMENTS_REGEX, SHIPMENTS_DESCRIPTION_STATUS)


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProductGet(BaseConfigModel):
    id: int
    model: str
    status: str


class ProductCreate(BaseConfigModel):
    model: str = fields.Field(max_length=255, min_length=3)
    status: str = fields.Field(min_length=5, default='IN_STOCK',
                               pattern=PRODUCT_REGEX,
                               description=PRODUCT_DESCRIPTION_STATUS)


class Warehouse(BaseConfigModel):
    ...


class ProductionBatchesPost(BaseConfigModel):
    product_id: str
    start_date: datetime.datetime = datetime.datetime.now(datetime.UTC)


class Shipment(BaseConfigModel):
    ...
