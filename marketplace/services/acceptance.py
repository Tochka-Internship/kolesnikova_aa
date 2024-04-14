import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import TypeAlias

from models import Acceptance, Item, Sku, Stock, StockStatus, Task, TaskType
from models import TaskStatus as DBTaskStatus
from providers.acceptance import AcceptanceProvider
from providers.sku import SkuProvider
from schemas.acceptance import (
    AcceptanceInfoResponseSkuByStockStatus,
    AcceptanceInfoTask,
    CreateAcceptanceRequest,
    CreateAcceptanceResponse,
    GetAcceptanceInfoResponse,
    StockStatusSchema,
    TaskStatus,
)
from sqlalchemy.ext.asyncio import AsyncSession
from utils.utils import revert_dict

SkuByStockStatusKey: TypeAlias = tuple[uuid.UUID, StockStatus]

# TODO: Перенести в мапперы
# TODO: Для Апи точно не нужен мапинг - нужно передавать поле как есть - проверить. Для БД - проверить
db_to_api_stock_status_map: dict[StockStatus, StockStatusSchema] = {
    StockStatus.VALID: StockStatusSchema.VALID,
    StockStatus.DEFECT: StockStatusSchema.DEFECT,
}

api_to_db_stock_status_map: dict[StockStatusSchema, StockStatus] = revert_dict(db_to_api_stock_status_map)
# TODO: В будущем убрать и изменить на отображение Модель API <- Модель сервиса <- Модель БД
task_status_model_to_api_map = {
    DBTaskStatus.COMPLETED: TaskStatus.COMPLETED,
    DBTaskStatus.IN_WORK: TaskStatus.IN_WORK,
    DBTaskStatus.CANCELED: TaskStatus.CANCELED,
}


@dataclass
class AcceptanceService:
    db_session_maker: Callable[[], AsyncSession]
    acceptance_provider: Callable[[AsyncSession], AcceptanceProvider] = AcceptanceProvider
    sku_provider: Callable[[AsyncSession], SkuProvider] = SkuProvider

    async def get_acceptance_info(self, id: uuid.UUID) -> GetAcceptanceInfoResponse:
        """Получить инфо о приемке"""
        async with self.db_session_maker() as session:
            acceptance: Acceptance = await self.acceptance_provider(session).find_one(id=id)

        # Получаем все задачи связанные с данной приемкой
        acceptance_tasks: list[Task] = [
            task
            for task in acceptance.tasks
            # Пока на всякий случай фильтруем задачи по типу
            # TODO: Добавить ограничение в таблице acceptances на тип задач только PLACING
            if task.type is TaskType.PLACING
        ]
        # Предполагаем что нам интересен прогресс обработанных/принятых товаров, а не просто все товары

        accepted_items_by_sku_stock_status: dict[SkuByStockStatusKey, list[Item]] = defaultdict(list)
        # Получаем все товары, связанные с данной приемкой в статусе завершено
        for task in acceptance_tasks:
            item: Item = task.item
            # Для удобства формируем ключ из ID SKU и статуса стока,
            # т.к. количество принятых товаров нужно выводит по SKU и типу стока
            key: SkuByStockStatusKey = (item.sku.id, item.stock.status)

            # Если задание по приемке товара не завершено, то пропускаем данный товар
            if task.status is not DBTaskStatus.COMPLETED:
                continue
            accepted_items_by_sku_stock_status[key].append(item)

        accepted_info = [
            AcceptanceInfoResponseSkuByStockStatus(
                sku_id=sku_id,
                stock=db_to_api_stock_status_map.get(stock_status),
                # TODO: Нужно динамически считать в зависимости от количества принятых товаров
                count=len(items),
            )
            for (sku_id, stock_status), items in accepted_items_by_sku_stock_status.items()
        ]

        return GetAcceptanceInfoResponse(
            id=acceptance.id,
            created_at=acceptance.created_at,
            accepted=accepted_info,
            task_ids=[
                AcceptanceInfoTask(
                    id=task.id,
                    status=task_status_model_to_api_map.get(task.status),
                )
                for task in acceptance_tasks
            ],
        )

    async def process_acceptance(self, acceptance_id: uuid.UUID) -> None:
        """Приемка товара

        Перевод задачи типа type=TaskType.PLACING в статус status=TaskStatus.COMPLETED
        и может быть перевод статуса в acceptance на completed
        """
        # Некоторое ожидание для правдоподобности тяжелого долгого фонового действия
        # await sleep(10)
        async with self.db_session_maker() as session:
            acceptance: Acceptance = await self.acceptance_provider(session).find_one(id=acceptance_id)
            # Предположим что в БД есть ограничения и таски приходят нужного типа
            # TODO: Реализовать это место, как будет понятно, как делать скидку дефектному товару и сколько
            for task in acceptance.tasks:
                # task: Task
                # item: Item = task.item
                # stock: Stock = item.stock
                # if stock.status is StockStatus.DEFECT:
                #     # TODO: Сделать скидку
                #     ...
                # ...
                task.status = TaskStatus.COMPLETED
            await session.commit()

    async def create_acceptance(self, request_data: CreateAcceptanceRequest) -> CreateAcceptanceResponse:
        """
        Создать задачу на приемку товара

        Приемка товара
        Приемка товара осуществляется в рамках задачи на приемку.
        При создании задачи на приемку создаются задачи на размещение товара.
        Приемка считается выполненной, когда в ней не осталось активных задач на размещение товара.
        В рамках приемки товары можно разместить в сток Valid или в Defect.
        При приемке товара, если указан несуществующий sku_id -
        необходимо автоматически создать новый SKU с базовой стоимостью 0.00.
        Максимальное кол-во товаров в рамках одного SKU - n < 1000 и n > 0.
        """
        async with self.db_session_maker() as session:
            acceptance = Acceptance()
            session.add(acceptance)
            # Получаем ID для последующей связи
            await session.flush()

            # # Резервирование товаров
            # for item in items:
            #     item.stock.is_reserved = True
            #     # Создание задач на подбор товара в рамках одного SKU
            #     task: Task = Task(
            #         status=TaskStatus.IN_WORK,
            #         type=TaskType.PICKING,
            #         posting=posting,
            #         item=item,
            #     )
            #     session.add(task)

            for sku_by_stock_type in request_data.items_to_accept:

                sku_provider = self.sku_provider(session)
                sku: Sku | None
                # Получаем SKU
                try:
                    sku = await sku_provider.find_one(id=sku_by_stock_type.sku_id)
                # TODO: Сузить исключение
                except Exception:
                    sku = None
                # Если SKU не существует, создаем его
                if not sku:
                    sku = Sku(
                        id=sku_by_stock_type.sku_id,
                        # TODO: Подумать над данным моментом
                        actual_price=Decimal("0.00"),
                        base_price=Decimal("0.00"),
                    )
                    session.add(sku)
                    # Выталкиваем для получение ID Sku
                    await session.flush()

                # TODO: Вынести в отдельную функцию create_items_by_sku_stocks
                items: list[Item] = [
                    Item(
                        sku=sku,
                        # TODO: Возможно придется вынести наверх и переделать в цикл вместо list comprehension
                        #  В целом можно и стоки вынести в list comprehension
                        stock=Stock(
                            status=api_to_db_stock_status_map.get(sku_by_stock_type.stock)
                        ),
                        acceptance=acceptance,
                    )
                    for _ in range(sku_by_stock_type.count)
                ]
                # TODO: Вынести в отдельную функцию create_tasks_by_items_to_placing
                tasks: list[Task] = [
                    Task(
                        status=TaskStatus.IN_WORK,
                        type=TaskType.PLACING,
                        acceptance=acceptance,
                        item=item
                    )
                    for item in items
                ]
                session.add_all(tasks)
                await session.commit()

                # TODO: Запустить фоном обработку приемки задач
                await self.process_acceptance(acceptance_id=acceptance.id)

        return CreateAcceptanceResponse(id=acceptance.id)
