import pytest
from factories.models.acceptance import AcceptanceFactoryBase
from factories.models.discount import DiscountFactoryBase
from factories.models.item import ItemFactoryBase
from factories.models.item_discount import ItemDiscountFactoryBase
from factories.models.posting import PostingFactoryBase
from factories.models.sku import SkuFactoryBase
from factories.models.stock import StockFactoryBase
from factories.models.task import TaskFactoryBase
from httpx import AsyncClient
from models import Item, Sku, Task, TaskStatus
from schemas.task import (
    FinishTaskRequest,
    FinishTaskStatus,
    GetTaskInfoResponse,
    TaskTarget,
)
from sqlalchemy.ext.asyncio import AsyncSession


class TestTaskApi:
    @pytest.fixture
    async def item(self, db: AsyncSession) -> Item:
        posting = PostingFactoryBase.build()
        return await ItemFactoryBase.create(
            sku=SkuFactoryBase.build(),
            stock=StockFactoryBase.build(),
            # posting=PostingFactoryBase.build(),
            # TODO: Сделать фабрику PickingTaskFactoryBase c Posting
            tasks=TaskFactoryBase.build_batch(5, posting=posting),
            acceptance=AcceptanceFactoryBase.build(),
            item_discounts=ItemDiscountFactoryBase.build_batch(5),
        )

    @pytest.fixture
    async def sku(
        self,
        db: AsyncSession,
        item: Item,
    ) -> Sku:
        return await SkuFactoryBase.create(
            discount=DiscountFactoryBase.build(),
            items=[item],
        )

    @pytest.fixture
    async def task(
        self,
        db: AsyncSession,
        sku: Sku,
    ) -> Task:
        return await TaskFactoryBase.create(
            status=TaskStatus.IN_WORK,
            item=ItemFactoryBase.build(
                sku=sku,
                stock=StockFactoryBase.build(),
                acceptance=AcceptanceFactoryBase.build(),
            )
        )

    async def test_get_task_info_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        task: Task,
    ):
        response = await client.get(
            url="/getTaskInfo",
            params={"id": task.id},
        )
        assert response.status_code == 200, response.text
        assert GetTaskInfoResponse(**response.json()) == GetTaskInfoResponse(
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

    # TODO: Написать тест на закрытие закрытого задания
    @pytest.mark.parametrize('status', list(FinishTaskStatus))
    async def test_finish_task_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        task: Task,
        status: FinishTaskStatus,
    ):
        request_data = FinishTaskRequest(
            id=task.id,
            status=status,
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/finishTask",
            content=payload_json,
        )
        assert response.status_code == 200, response.text
