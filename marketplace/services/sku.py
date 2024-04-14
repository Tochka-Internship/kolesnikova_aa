import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from models import (
    Item,
    ItemDiscount,
    ItemDiscountType,
    PostingStatus,
    Sku,
    Task,
    TaskStatus,
    TaskType,
)
from models import (
    StockStatus as DBStockStatus,
)
from providers.item import ItemProvider
from providers.sku import SkuProvider
from schemas.sku import (
    GetItemInfoBySkuIdResponse,
    GetItemInfoResponse,
    GetSkuInfoResponse,
    ItemInfo,
    MarkdownItemRequest,
    MoveToNotFoundRequest,
    SetSkuPriceRequest,
    StockStatus,
    ToggleIsHiddenRequest,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

# TODO: подумать над маппингом
get_item_info_stock_status_db_to_api_map = {
    DBStockStatus.VALID: StockStatus.VALID,
    DBStockStatus.DEFECT: StockStatus.DEFECT,
    DBStockStatus.NOT_FOUND: StockStatus.NOT_FOUND,
}


@dataclass
class SkuService:
    db_session_maker: Callable[[], AsyncSession]
    sku_provider: Callable[[AsyncSession], SkuProvider] = SkuProvider
    item_provider: Callable[[AsyncSession], ItemProvider] = ItemProvider

    async def get_item_info(self, item_id: uuid.UUID) -> GetItemInfoResponse:
        async with self.db_session_maker() as session:
            item: Item = await self.item_provider(session).find_one(**{"id": item_id})
        return GetItemInfoResponse(
            id=item.id,
            sku_id=item.sku_id,
            stock=get_item_info_stock_status_db_to_api_map.get(item.stock.status),
            reserved_state=item.stock.is_reserved,
        )

    async def get_sku_info(self, sku_id: uuid.UUID) -> GetSkuInfoResponse:
        async with self.db_session_maker() as session:
            sku = await self.sku_provider(session).find_one(id=sku_id)
        return GetSkuInfoResponse(
            id=sku.id,
            created_at=sku.created_at,
            actual_price=sku.actual_price,
            base_price=sku.base_price,
            count=sku.count,
            is_hidden=sku.is_hidden,
        )

    async def get_item_info_by_sku_id(self, sku_id: uuid.UUID) -> GetItemInfoBySkuIdResponse:
        async with self.db_session_maker() as session:
            # items = await self.item_provider(session).find_one(**{"id": id})
            # TODO: Вынести в провайдер
            stmt = select(Item).filter_by(
                sku_id=sku_id,
            ).options(
                joinedload('*')
            )
            res = await session.execute(stmt)
            items: Sequence[Item] = res.unique().scalars().all()
        return GetItemInfoBySkuIdResponse(
            items=[
                ItemInfo(
                    item_id=item.id,
                    stock=get_item_info_stock_status_db_to_api_map.get(item.stock.status),
                    reserved_state=item.stock.is_reserved,
                )
                for item in items
            ]
        )

    async def update_sku_actual_price(self, sku_id: uuid.UUID) -> None:
        async with self.db_session_maker() as session:
            sku: Sku = await self.sku_provider(session).find_one(id=sku_id)
            # TODO: Переделать. Есть смысл делать только после перехода на Many To Many связь
            # max_sku_discount: SkuDiscount | None = None
            # for sku_discount in sku.discounts:
            #     if max_sku_discount is None or sku_discount.percentage > max_sku_discount.percentage:
            #         max_sku_discount = sku_discount
            # Так как в данный момент на каждый sku только по одной скидке, то можем сделать только так
            max_sku_discount = sku.discount
            # Если скидка присутствует, то применяем её
            if max_sku_discount:
                # Применяем максимальную скидку
                coefficient = (Decimal("100.00") - Decimal(max_sku_discount.percentage)) / Decimal("100.00")
                sku.actual_price = sku.base_price * coefficient
                await session.commit()

    async def update_skus_actual_prices(self, sku_ids: list[uuid.UUID]) -> None:
        for sku_id in sku_ids:
            await self.update_sku_actual_price(sku_id=sku_id)

    async def markdown_item(self, request_data: MarkdownItemRequest) -> None:
        """
        В каждый момент времени, любой из товаров можно признать дефектным,
        после чего применить ĸ нему указанную скидку.
        Если товар участвует в заказе -
        в рамках заказа должна быть создана задача на подбор аналогичного,
        если аналогичного товара - нет,
        то необходимо исключить из заказа этот товар и собирать оставшийся заказ."""
        async with self.db_session_maker() as session:
            # TODO: Продумать случай повторного признания товара дефектным.
            #  Пока предположим у товара может быть несколько дефектов
            item: Item = await self.item_provider(session).find_one(id=request_data.id)

            item_discount: ItemDiscount = ItemDiscount(
                type=ItemDiscountType.BY_DEFECT,
                percentage=int(request_data.percentage * 100) % 100,
                item=item,
            )
            # Скидку есть смысл добавлять только в случае, когда товар находится в корректных состояниях, а именно:
            # TODO: Вернуться к продумыванию корректных состояний, чтобы не добавлять скидку в ненужных состояниях
            session.add(item_discount)

            tasks: list[Task] = item.tasks
            picking_tasks: list[Task] = [
                task
                for task in tasks
                # Для упрощения не рассматриваем сейчас промежуточный вариант,
                # когда заказ собран, но не отправлен
                if task.type is TaskType.PICKING and task.status not in [TaskStatus.CANCELED, TaskStatus.COMPLETED]
            ]
            if len(picking_tasks) > 1:
                raise Exception("Некорректное состояние товара")
            if not picking_tasks:
                return

            # Если есть активная задача на подбор, то отменяем её и создаем новую
            if len(picking_tasks) == 1:
                picking_task: Task = picking_tasks[0]
                # Нет смысла добавлять задачу в случае конечных статусов заказа
                if picking_task.posting.status is PostingStatus.IN_ITEM_PICK:
                    picking_task.status = TaskStatus.CANCELED

                    new_picking_task: Task = Task(
                        status=TaskStatus.IN_WORK,
                        type=TaskType.PICKING,
                        posting=picking_task.posting,
                        item=item
                    )
                    session.add(new_picking_task)

            await session.commit()

    async def set_sku_price(self, request_data: SetSkuPriceRequest) -> None:
        async with self.db_session_maker() as session:
            # TODO: Сделать пересчет актуальной цены согласно дискаунтам
            await self.sku_provider(session).edit_one(
                id=request_data.sku_id,
                data={
                    "base_price": request_data.base_price,
                }
            )
            await session.commit()

    async def toggle_is_hidden(self, request_data: ToggleIsHiddenRequest) -> None:
        """Скрыть или отобразить товар для покупки"""
        # TODO: Возможно тут стоит продумать момент с отменой товаров с заказах,
        #  которые еще не отправлены и находятся на сборке
        async with self.db_session_maker() as session:
            await self.sku_provider(session).edit_one(
                id=request_data.sku_id,
                data={
                    "is_hidden": request_data.is_hidden,
                }
            )
            await session.commit()

    async def move_to_not_found(self, request_data: MoveToNotFoundRequest) -> None:
        async with self.db_session_maker() as session:
            item = await self.item_provider(session).find_one(id=request_data.id)
            item.stock.status = DBStockStatus.NOT_FOUND
            session.add(item)
            await session.commit()
