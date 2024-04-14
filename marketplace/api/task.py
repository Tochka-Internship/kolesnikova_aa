import uuid
from typing import Any

from api.dependencies import get_db
from fastapi import APIRouter, Depends, Query
from schemas.task import FinishTaskRequest, GetTaskInfoResponse
from services.task import TaskService
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

router = APIRouter(
    tags=["Task"],
)


@router.get("/getTaskInfo", response_model=GetTaskInfoResponse)
async def get_task_info(
    id: uuid.UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> GetTaskInfoResponse:
    """Получение деталей задачи по ID"""
    return await TaskService(
        db_session_maker=lambda: db,
    ).get_task_info(task_id=id)


@router.post("/finishTask", status_code=status.HTTP_200_OK)
async def finish_task(
    request_data: FinishTaskRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Завершение задачи"""
    await TaskService(
        db_session_maker=lambda: db,
    ).finish_task(request_data=request_data)
    return status.HTTP_200_OK
