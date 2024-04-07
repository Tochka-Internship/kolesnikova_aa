from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel


class TaskStatus(StrEnum):
    COMPLETED = "completed"
    IN_WORK = "in_work"
    CANCELED = "canceled"


class TaskType(StrEnum):
    PLACING = "placing"
    PICKING = "picking"


class TaskTargetStockStatus(StrEnum):
    VALID = "valid"
    DEFECT = "defect"
    # NOTE: Несоответствие статусов в модели и в схеме API,
    #  что приведет к падению в случае получения статуса NotFound,
    #  который считаю легитимным
    NOT_FOUND = "notfound"


class TaskTarget(BaseModel):
    id: UUID
    stock: TaskTargetStockStatus


class GetTaskInfoResponse(BaseModel):
    id: UUID
    status: TaskStatus
    created_at: AwareDatetime
    type: TaskType
    task_target: TaskTarget
    # TODO: Уточнить что имелось в виду под "posting_id": "uuid?"
    posting_id: UUID | None


class FinishTaskStatus(StrEnum):
    COMPLETED = "completed"
    CANCELED = "canceled"


class FinishTaskRequest(BaseModel):
    id: UUID
    status: FinishTaskStatus
