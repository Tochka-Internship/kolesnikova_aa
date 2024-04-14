from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field


class StockStatusSchema(StrEnum):
    VALID = "valid"
    DEFECT = "defect"


class AcceptanceInfoSkuByStockStatus(BaseModel):
    sku_id: UUID
    stock: StockStatusSchema
    count: int = Field(gt=0, lt=1000)


class AcceptanceInfoResponseSkuByStockStatus(AcceptanceInfoSkuByStockStatus):
    # NOTE: Отличается от входной тем, что нет валидации ответа,
    # таким образом уменьшаем вероятность падения на стороне сервера
    count: int


class TaskStatus(StrEnum):
    COMPLETED = "completed"
    IN_WORK = "in_work"
    CANCELED = "canceled"


class AcceptanceInfoTask(BaseModel):
    id: UUID
    status: TaskStatus


class GetAcceptanceInfoResponse(BaseModel):
    id: UUID
    created_at: AwareDatetime
    accepted: list[AcceptanceInfoResponseSkuByStockStatus] = Field(default_factory=list)
    task_ids: list[AcceptanceInfoTask] = Field(default_factory=list)


class CreateAcceptanceRequest(BaseModel):
    items_to_accept: list[AcceptanceInfoSkuByStockStatus] = Field(default_factory=list)


class CreateAcceptanceResponse(BaseModel):
    id: UUID
