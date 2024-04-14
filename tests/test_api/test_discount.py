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
from models import Discount, Item, Sku
from schemas.discount import (
    CancelDiscountSchema,
    CreateDiscountResponseSchema,
    CreateDiscountSchema,
    DiscountSchema,
)
from sqlalchemy.ext.asyncio import AsyncSession


class TestDiscountApi:
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
    async def discount(
        self,
        db: AsyncSession,
        item: Item,
    ) -> Discount:
        return await DiscountFactoryBase.create(
            skus=SkuFactoryBase.build_batch(5),
            item_discounts=ItemDiscountFactoryBase.build_batch(
                size=5,
                item=item,
            ),
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

    async def test_get_discount_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        discount: Discount,
    ):
        response = await client.get(
            url="/getDiscount",
            params={"id": discount.id},
        )
        assert response.status_code == 200, response.text
        assert DiscountSchema(**response.json())

    @pytest.mark.parametrize('percentage', [1, 10, 50, 99])
    async def test_create_discount_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        sku: Sku,
        percentage: int,
    ):
        request_data = CreateDiscountSchema(
            sku_ids=[sku.id],
            percentage=percentage,
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/createDiscount",
            content=payload_json,
        )
        assert response.status_code == 201, response.text
        assert CreateDiscountResponseSchema(**response.json())

    async def test_cancel_discount_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        discount: Discount,
    ):
        request_data = CancelDiscountSchema(
            id=discount.id,
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/cancelDiscount",
            content=payload_json,
        )
        assert response.status_code == 200, response.text
