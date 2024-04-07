import datetime
import enum
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BaseDTOModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SkuDTO(BaseDTOModel):
    id: uuid.UUID
    created_at: datetime.datetime
    actual_price: Decimal
    base_price: Decimal
    count: int
    is_hidden: bool


class DiscountStatusDTO(enum.StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"


class DiscountDTO(BaseDTOModel):
    id: uuid.UUID
    status: DiscountStatusDTO
    created_at: datetime.datetime
    percentage: int
    skus: list["SkuDTO"] = Field(default_factory=list)


class CreateDiscountDTO(BaseModel):
    sku_ids: list[uuid.UUID] = Field(default_factory=list)
    percentage: int = Field(gt=0, lt=100)
