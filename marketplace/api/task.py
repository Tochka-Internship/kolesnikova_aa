import uuid
from typing import Any

from app.database import async_session_maker
from fastapi import APIRouter, Query
from schemas.task import FinishTaskRequest, GetTaskInfoResponse
from services.task import TaskService
from starlette import status

router = APIRouter(
    tags=["Task"],
)


@router.get("/getTaskInfo", response_model=GetTaskInfoResponse)
async def get_task_info(
    id: uuid.UUID = Query(),
) -> GetTaskInfoResponse:
    """Получение деталей задачи по ID"""
    return await TaskService(
        db_session_maker=async_session_maker,
    ).get_task_info(task_id=id)


@router.post("/finishTask", status_code=status.HTTP_200_OK)
async def finish_task(
    request_data: FinishTaskRequest,
) -> Any:
    """Завершение задачи"""
    await TaskService(
        db_session_maker=async_session_maker,
    ).finish_task(request_data=request_data)
    return status.HTTP_200_OK
