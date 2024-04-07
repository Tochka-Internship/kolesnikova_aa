import uuid
from collections.abc import Callable
from dataclasses import dataclass

from models import Task, TaskStatus
from providers.task import TaskProvider
from schemas.task import FinishTaskRequest, GetTaskInfoResponse, TaskTarget
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class TaskService:
    db_session_maker: Callable[[], AsyncSession]
    task_provider: Callable[[AsyncSession], TaskProvider] = TaskProvider

    async def get_task_info(self, task_id: uuid.UUID) -> GetTaskInfoResponse:
        """Получение деталей задачи по ID"""
        async with self.db_session_maker() as session:
            task: Task = await self.task_provider(session).find_one(id=task_id)
        return GetTaskInfoResponse(
            id=task.id,
            status=task.status,
            created_at=task.created_at,
            type=task.type,
            task_target=TaskTarget(
                id=task.item.stock.id,
                # TODO: Не самое лучшее отображение статусов БД в статусы API
                stock=task.item.stock.status.value.lower(),
            ),
            posting_id=task.posting_id,
        )

    async def finish_task(self, request_data: FinishTaskRequest) -> None:
        """Завершение задачи"""
        async with self.db_session_maker() as session:
            task: Task = await self.task_provider(session).find_one(id=request_data.id)
            # TODO: Подумать что делать с отображением статусов API в БД
            # Предусматриваем что нельзя перевести задачу из одного закрытого в статус в другой,
            # если это не тот же статус
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELED] and task.status != request_data.status:
                raise Exception(f"Вы не можете завершить задание со статусом {task.status}")
            task.status = request_data.status
            await session.commit()
