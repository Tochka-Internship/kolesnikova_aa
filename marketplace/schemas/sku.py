import enum
from decimal import Decimal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field


class StockStatus(enum.Enum):
    VALID = "valid"
    DEFECT = "defect"
    NOT_FOUND = "not_found"


class GetItemInfoResponse(BaseModel):
    id: UUID
    sku_id: UUID
    stock: StockStatus
    reserved_state: bool


class GetSkuInfoResponse(BaseModel):
    id: UUID
    created_at: AwareDatetime
    actual_price: Decimal = Field(ge=0)
    base_price: Decimal = Field(ge=0)
    count: int
    is_hidden: bool


class ItemInfo(BaseModel):
    item_id: UUID
    stock: StockStatus
    reserved_state: bool


class GetItemInfoBySkuIdResponse(BaseModel):
    items: list[ItemInfo] = Field(default_factory=list)


class MarkdownItemRequest(BaseModel):
    id: UUID
    percentage: Decimal = Field(ge=0, le=1)


class SetSkuPriceRequest(BaseModel):
    sku_id: UUID
    base_price: Decimal = Field(ge=0)


class ToggleIsHiddenRequest(BaseModel):
    sku_id: UUID
    is_hidden: bool


class MoveToNotFoundRequest(BaseModel):
    id: UUID
