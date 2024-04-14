import uuid
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from itertools import chain

from models import (
    Item,
    ItemDiscount,
    Posting,
    PostingStatus,
    Sku,
    Stock,
    StockStatus,
    Task,
    TaskStatus,
    TaskType,
)
from models import StockStatus as DBStockStatus
from providers.item import ItemProvider
from providers.posting import PostingProvider
from schemas.posting import (
    CancelPostingRequest,
    CreatePostingRequest,
    CreatePostingResponse,
    GetPostingResponse,
    OrderedGood,
    TaskSchema,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


@dataclass
class PostingService:
    db_session_maker: Callable[[], AsyncSession]
    posting_provider: Callable[[AsyncSession], PostingProvider] = PostingProvider
    item_provider: Callable[[AsyncSession], ItemProvider] = ItemProvider

    async def get_posting(self, posting_id: uuid.UUID) -> GetPostingResponse:
        """Получение информации по заказу"""
        async with self.db_session_maker() as session:
            posting: Posting = await self.posting_provider(session).find_one(id=posting_id)

        items_by_not_hided_sku: dict[uuid.UUID, list[Item]] = defaultdict(list)
        # items_by_hided_sku: dict[uuid.UUID, list[Item]] = defaultdict(list)

        # TODO: Сделать получение не найденных товаров из списка товаров отмененных задач
        #  + возможно стоит добавить дополнительное условие и не показывать товары, по которым была замена
        for item in posting.items:
            # NOTE: Так как пока решено не прикреплять изначально заказанные товары к заказу,
            # (такие товары можно найти в задачах на подбор), то нет смысла использовать здесь логику sku.is_hidden
            # if item.sku.is_hidden:
            #     items_by_hided_sku[item.sku.id].append(item)
            #     continue
            items_by_not_hided_sku[item.sku.id].append(item)

        # Находим не найденные товары из списка отмененных задач на подбор товара
        # TODO: Скорректировать, убрав из списка успешно замененные товары
        not_found_sku_ids: list[uuid.UUID] = [
            task.item.id
            for task in posting.tasks
            if task.type is TaskType.PICKING and task.statis is TaskStatus.CANCELED
        ]

        return GetPostingResponse(
            id=posting.id,
            status=posting.status,
            created_at=posting.created_at,
            # NOTE: Цена просчитывается с учетом всех скидок в процессе сбора заказа
            cost=posting.cost,
            ordered_goods=[
                OrderedGood(
                    sku=sku_id,
                    from_valid_ids=[item.id for item in items if item.stock.status is DBStockStatus.VALID],
                    from_defect_ids=[item.id for item in items if item.stock.status is DBStockStatus.DEFECT],
                )
                for sku_id, items in items_by_not_hided_sku.items()
            ],
            # TODO: Посмотреть по ходу точно ли понятен смысл данного поля
            # TODO: Подумать в какой момент влияет сокрытие SKU.
            #  На данный момент кажется что в момент создания заказа
            not_found=not_found_sku_ids,
            task_ids=[
                TaskSchema(
                    id=task.id,
                    type=task.type,
                    status=task.status,
                )
                for task in posting.tasks
            ],
        )

    async def process_picking_posting(
        self,
        posting_id: uuid.UUID,
        discount_percent_by_defect: int = 5,
    ) -> None:
        """Процесс сбора заказа (обработка задач на сборку заказа)

        Сбор заказа
        Массив задач, в которых указан ID товара, который надо подобрать.
        Во время сборки заказа товар может быть утерян.
        Если товар потерян - должна быть создана задача на подбор нового аналогичного товара,
        а текущий товар перемещен на сток NotFound.
        Если альтернативного товара нет и подобрать другой товар невозможно -
        заказ должен быть собран без этого товара.
        Текущей задаче проставляется статус Canceled.
        """
        async with self.db_session_maker() as session:
            # Получаем заказ
            posting: Posting = await self.posting_provider(session).find_one(id=posting_id)
            # Цикл сделан для удобства, чтобы повторно не вызывать process_posting и собрать все товары за раз,
            # в случае с добавлением задач на подбор потерянного товара
            while True:
                # Обновляем для получения актуального статуса задач
                # await session.refresh(posting)
                await session.refresh(
                    posting,
                    # Указываем какие связи необходимо обновить, иначе будет ошибка
                    attribute_names=[
                        "tasks",
                        "items",
                    ]
                )
                # Получаем актуальные задачи на сбор
                picking_tasks_to_process: list[Task] = [
                    task
                    for task in posting.tasks
                    if task.type is TaskType.PICKING and task.status is TaskStatus.IN_WORK
                ]
                # Если нет актуальных задач на подбор, то прерываем цикл
                if not picking_tasks_to_process:
                    break
                # Обрабатываем заказ
                task: Task
                for task in picking_tasks_to_process:
                    item: Item = task.item
                    stock: Stock = item.stock
                    sku: Sku = item.sku
                    # Если SKU товара скрыт, было решено просто закрывать задачу на сбор
                    if sku.is_hidden:
                        # Отменяем текущую задачу
                        task.status = TaskStatus.CANCELED
                        # TODO: Добавить причину отмены?
                        #  Так как она нигде не выводится и нам запрещено изменять контракт API,
                        #  то в рамках поставленной задачи от подобного поля нет смысла
                        # Добавляем изменение по текущей задаче
                        await session.commit()
                        continue

                    if stock.status is StockStatus.VALID:
                        # Здесь пока ничего не требуется делать, статус собранной задачи отображен ниже
                        ...
                    elif stock.status is StockStatus.NOT_FOUND:
                        # TODO:
                        # await self.item_provider(session).find_unreserved_one(
                        #     sku_id=sku.id,
                        # )

                        # Получаем незарезервированный товар
                        query = (
                            select(Item).filter(
                                Stock.is_reserved is False,
                                # TODO: Здесь бы стоило найти товар того же качества, но это требует бОльших доработок
                                Stock.status is not StockStatus.NOT_FOUND,
                            )
                        )
                        item_for_change: Item | None = (await session.execute(query)).scalar()
                        # Если такой товар есть, то создаем задачу на сбор
                        if item_for_change:
                            task_for_change: Task = Task(
                                status=TaskStatus.IN_WORK,
                                type=TaskType.PICKING,
                                posting=posting,
                                item=item_for_change,
                            )
                            session.add(task_for_change)
                        # Отменяем текущую задачу
                        task.status = TaskStatus.CANCELED
                        # Добавляем изменение по текущей задаче и добавляем задачу на подбор аналогичного товара
                        await session.commit()
                        continue
                    elif stock.status is StockStatus.DEFECT:
                        # TODO: Вынести в сервис по применению скидок?
                        ...
                    # Привязываем данный товар за текущим заказом
                    item.posting = posting
                    # Задача обработана
                    task.status = TaskStatus.COMPLETED
                    await session.commit()

                await session.commit()
            # Получаем актуальное состояние заказа
            await session.refresh(
                posting,
                # Указываем какие связи необходимо обновить, иначе будет ошибка
                attribute_names=[
                    "tasks",
                    "items",
                ]
            )
            # Проверяем собран ли заказ - для этого все задачи должны быть завершены
            is_assembled = all([task.status is TaskStatus.COMPLETED for task in posting.tasks])
            if is_assembled:
                # Формируем цену заказа
                actual_posting_price: Decimal = Decimal("0.00")
                item: Item
                # Если так получилось,
                # что не удалось подобрать никаких товаров,
                # то заказ нужно отменить - иначе это не имеет никакого смысла
                if not posting.items:
                    posting.status = PostingStatus.CANCELED
                    await session.commit()
                    return
                for item in posting.items:
                    # Находим максимальную скидку
                    # TODO: Вынести в функцию получения максимальной скидки
                    max_item_discount: ItemDiscount | None = None
                    for item_discount in item.item_discounts:
                        if max_item_discount is None or item_discount.percentage > max_item_discount.percentage:
                            max_item_discount = item_discount
                    sku: Sku = item.sku
                    item_cost = sku.base_price
                    # Если скидка присутствует, то применяем её
                    if max_item_discount:
                        # Применяем максимальную скидку
                        coefficient = (Decimal("100.00") - Decimal(max_item_discount.percentage)) / Decimal("100.00")
                        item_cost = sku.base_price * coefficient
                    # Суммируем с остальной стоимостью заказа
                    actual_posting_price += item_cost

                # Обновляем стоимость заказа
                posting.cost = actual_posting_price
                # Предполагаем что сразу по завершению сборки идет отправка и заказ отправлен,
                # без промежуточного процесса
                posting.status = PostingStatus.SENT
                await session.commit()

    async def create_posting(self, request_data: CreatePostingRequest) -> CreatePostingResponse:
        """
        Создание заказа
        Пользователь выбирает определенные товары, после чего заказывает их.
        Создаются задачи на сбор заказа, на каждый конкретный ID товара - отдельная задача.
        Товар, на который создана задача должен быть зарезервирован.
        """

        # """
        # Сбор заказа
        # Массив задач, в которых указан ID товара, который надо подобрать.
        # Во время сборки заказа товар может быть утерян.
        # Если товар потерян - должна быть создана задача на подбор нового аналогичного товара,
        # а текущий товар перемещен на сток NotFound.
        # Если альтернативного товара нет и подобрать другой товар
        # невозможно - заказ должен быть собран без этого товара.
        # Текущей задаче проставляется статус Canceled.
        # """
        async with self.db_session_maker() as session:
            # Предсоздаем заказ
            posting: Posting = Posting(
                # TODO: Возможно стоит сделать статус NEW и сделать его по умолчанию
                status=PostingStatus.IN_ITEM_PICK,
                # TODO: Подумать над моментом подсчета цены
                cost=Decimal("0.00"),
            )
            # Добавляем и выталкиваем его в БД, чтобы получить ID для последующей связки с товарами и задачами
            session.add(posting)
            await session.flush()

            for ordered_goods_by_sku in request_data.ordered_goods:
                # Если SKU скрыт, то это уже проблема сбора заказа.
                # Только вот вопрос, а точно ли так?
                # Тут выбор между:
                # возможностью покупателя гарантировано получить товар
                # и
                # возможностью продавца отозвать свой товар.
                # Так как товар мы все равно можем не найти, а отзываться может:
                # либо опасный товар,
                # либо некорректно сформированный товар,
                # то оставим отмену скрытых позиций на момент сбора заказа

                # Выбираем все стоки товара
                query = (
                    select(Item)
                    .filter(
                        # https://docs-python.ru/standart-library/modul-itertools-python/funktsija-chain-modulja
                        # -itertools/
                        Item.id.in_(chain(
                            ordered_goods_by_sku.from_valid_ids,
                            ordered_goods_by_sku.from_defect_ids,
                        ))
                    )
                    .options(
                        joinedload(Item.sku),
                        joinedload(Item.stock),
                    )
                    # # Блокируем стоки товара на обновление, чтобы только мы могли их зарезервировать
                    # .with_for_update(
                    #     # of=Stock,
                    # )
                )
                # Получение товаров
                items: Sequence[Item] = (await session.execute(query)).scalars().all()
                # TODO: Предусмотреть выброс ошибки, если товары не найдены полностью или частично?

                # Резервирование товаров
                for item in items:
                    item.stock.is_reserved = True
                    # Создание задач на подбор товара в рамках одного SKU
                    task: Task = Task(
                        status=TaskStatus.IN_WORK,
                        type=TaskType.PICKING,
                        posting=posting,
                        item=item,
                    )
                    session.add(task)
                # TODO: Должна ли быть привязка товаров в создании заказа? Пока думаю что нет
                await session.commit()
            # TODO: Вынести в фоновую задачу
            await self.process_picking_posting(posting_id=posting.id)

        return CreatePostingResponse(id=posting.id)

    async def process_cancel_posting(
        self,
        posting_id: uuid.UUID,
    ):
        """Процесс обработки отмены заказа"""
        # TODO: Сделать процесс обработки отмены заказа
        ...

    async def cancel_posting(self, request_data: CancelPostingRequest) -> None:
        """
        Отмена заказа
        До момента, когда заказ отправлен (проставлен статус Sent) - пользователь может отменить заказ.
        Должны быть созданы задачи на размещение, которые снимут резерв с товара, вернут его на стоки.
        """
        async with self.db_session_maker() as session:
            posting: Posting = await self.posting_provider(session).find_one(id=request_data.id)
            if posting.status is PostingStatus.SENT:
                raise Exception("Заказ невозможно отменить.\nПричина: Заказ отправлен")
            elif posting.status is PostingStatus.SENT:
                # Если заказ отменен, то нет смысла делать что-либо, разве что добавить логгирование?
                return
            for item in posting.items:
                # TODO: В процессах описано что именно задачи снимут резерв - подумать над этим
                # Снятие резерва с товара
                item.stock.is_reserved = False
                # Создание задач на подбор товара в рамках одного SKU
                task: Task = Task(
                    status=TaskStatus.IN_WORK,
                    type=TaskType.PLACING,
                    posting=posting,
                    item=item,
                )
                session.add(task)
            posting.status = PostingStatus.CANCELED
            await session.commit()
            # TODO: Вынести в фоновую задачу
            await self.process_cancel_posting(posting_id=posting.id)
        return
