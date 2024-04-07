import uuid
from decimal import Decimal
from enum import StrEnum
from typing import TypeAlias

from pydantic import AwareDatetime, BaseModel, Field

item_uuid: TypeAlias = uuid.UUID
sku_id: TypeAlias = uuid.UUID


class PostingStatus(StrEnum):
    in_item_pick = "in_item_pick"
    sent = "sent"
    canceled = "canceled"


class OrderedGood(BaseModel):
    sku: uuid.UUID
    from_valid_ids: list[item_uuid] = Field(default_factory=list)
    from_defect_ids: list[item_uuid] = Field(default_factory=list)


class TaskType(StrEnum):
    placing = "placing"
    picking = "picking"


class TaskStatus(StrEnum):
    completed = "completed"
    in_work = "in_work"
    canceled = "canceled"


class TaskSchema(BaseModel):
    id: uuid.UUID
    type: TaskType
    status: TaskStatus


class GetPostingResponse(BaseModel):
    id: uuid.UUID
    status: PostingStatus
    created_at: AwareDatetime
    cost: Decimal = Field(ge=0)
    ordered_goods: list[OrderedGood] = Field(default_factory=list)
    not_found: list[sku_id] = Field(default_factory=list)
    task_ids: list[TaskSchema] = Field(default_factory=list)


class CreatePostingRequest(BaseModel):
    ordered_goods: list[OrderedGood] = Field(default_factory=list)


class CreatePostingResponse(BaseModel):
    id: uuid.UUID


class CancelPostingRequest(BaseModel):
    id: uuid.UUID
