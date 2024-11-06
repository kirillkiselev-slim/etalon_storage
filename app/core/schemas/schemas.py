import datetime
from decimal import Decimal
from typing import Dict, Annotated

from pydantic import BaseModel, fields, conint, ConfigDict


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Product(BaseConfigModel):
    id: int
    model: str
    status: str


class Warehouse(BaseConfigModel):
    ...


class ProductionBatchesPost(BaseConfigModel):
    product_id: str
    start_date: datetime.datetime = datetime.datetime.now(datetime.UTC)


class Shipment(BaseConfigModel):
    ...
