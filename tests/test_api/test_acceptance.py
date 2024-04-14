import pytest
from factories.models.acceptance import AcceptanceFactoryBase
from factories.models.item import ItemFactoryBase
from factories.models.item_discount import ItemDiscountFactoryBase
from factories.models.posting import PostingFactoryBase
from factories.models.sku import SkuFactoryBase
from factories.models.stock import StockFactoryBase
from factories.models.task import TaskFactoryBase
from factories.schemas.acceptance import (
    AcceptanceInfoSkuByStockStatusFactory,
    CreateAcceptanceRequestFactory,
)
from httpx import AsyncClient
from models import Acceptance, Item
from schemas.acceptance import CreateAcceptanceRequest, GetAcceptanceInfoResponse
from sqlalchemy.ext.asyncio import AsyncSession


class TestAcceptanceApi:
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
    async def acceptance(
        self,
        db: AsyncSession,
        item: Item,
    ) -> Acceptance:
        return await AcceptanceFactoryBase.create(
            items=[item],
        )

    async def test_get_acceptance_info_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        acceptance: Acceptance,
    ):
        response = await client.get(
            url="/getAcceptanceInfo",
            params={"id": acceptance.id},
        )
        assert response.status_code == 200, response.text
        assert GetAcceptanceInfoResponse(**response.json())

    @pytest.mark.parametrize('items_count', [1, 5, 10])
    @pytest.mark.parametrize('stock_count_per_item', [1, 5, 10])
    async def test_create_acceptance_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        items_count: int,
        stock_count_per_item: int,
    ):
        # TODO: Проверить количество создаваемых записей
        # TODO: Написать тест на нулевое количество
        request_data: CreateAcceptanceRequest = CreateAcceptanceRequestFactory(
            items_to_accept=AcceptanceInfoSkuByStockStatusFactory.build_batch(
                size=items_count,
                count=stock_count_per_item,
            ),
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/createAcceptance",
            content=payload_json,
        )
        assert response.status_code == 201, response.text
