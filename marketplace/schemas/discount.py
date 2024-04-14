import uuid
from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, Field


class DiscountSchemaStatus(StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"


class DiscountSchema(BaseModel):
    id: uuid.UUID
    status: DiscountSchemaStatus
    created_at: AwareDatetime
    percentage: int
    sku_ids: list[uuid.UUID] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CreateDiscountSchema(BaseModel):
    sku_ids: list[uuid.UUID]
    percentage: int = Field(gt=0, lt=100)


class CreateDiscountResponseSchema(BaseModel):
    id: uuid.UUID


class CancelDiscountSchema(BaseModel):
    id: uuid.UUID
