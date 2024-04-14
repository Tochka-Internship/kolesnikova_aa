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
from models import Item, Sku
from schemas.sku import (
    GetItemInfoBySkuIdResponse,
    GetItemInfoResponse,
    GetSkuInfoResponse,
    ItemInfo,
    MarkdownItemRequest,
    MoveToNotFoundRequest,
    SetSkuPriceRequest,
    ToggleIsHiddenRequest,
)
from services.sku import get_item_info_stock_status_db_to_api_map
from sqlalchemy.ext.asyncio import AsyncSession


class TestSkuApi:
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

    async def test_get_item_info_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        item: Item,
    ):
        response = await client.get(
            url="/getItemInfo",
            params={"id": item.id},
        )
        assert response.status_code == 200, response.text
        assert GetItemInfoResponse(**response.json()) == GetItemInfoResponse(
            id=item.id,
            sku_id=item.sku_id,
            stock=get_item_info_stock_status_db_to_api_map.get(item.stock.status),
            reserved_state=item.stock.is_reserved,
        )

    async def test_get_sku_info_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        sku: Sku,
    ):
        response = await client.get(
            url="/getSkuInfo",
            params={"id": sku.id},
        )
        assert response.status_code == 200, response.text
        assert GetSkuInfoResponse(**response.json()) == GetSkuInfoResponse(
            id=sku.id,
            created_at=sku.created_at,
            actual_price=sku.actual_price,
            base_price=sku.base_price,
            count=sku.count,
            is_hidden=sku.is_hidden,
        )

    async def test_get_item_info_by_sku_id_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        sku: Sku,
    ):
        response = await client.get(
            url="/getItemInfoBySkuId",
            params={"id": sku.id},
        )
        items: list[Item] = sku.items

        assert response.status_code == 200, response.text
        assert GetItemInfoBySkuIdResponse(**response.json()) == GetItemInfoBySkuIdResponse(
            items=[
                ItemInfo(
                    item_id=item.id,
                    stock=get_item_info_stock_status_db_to_api_map.get(item.stock.status),
                    reserved_state=item.stock.is_reserved,
                )
                for item in items
            ]
        )

    async def test_markdown_item_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        item: Item,
    ):
        # TODO: Стабилизировать тест или сделать его юнит тестом
        request_data = MarkdownItemRequest(
            id=item.id,
            percentage='0.5',
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/markdownItem",
            content=payload_json,
        )
        # TODO: Написать проверку на выполненные действия
        # TODO: Сложная логика - нужно тестировать отдельно сервис
        assert response.status_code == 200, response.text

    async def test_set_sku_price_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        sku: Sku,
    ):
        request_data = SetSkuPriceRequest(
            sku_id=sku.id,
            base_price='1000.50'
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/setSkuPrice",
            content=payload_json,
        )
        assert response.status_code == 200, response.text

    @pytest.mark.parametrize('is_hidden', [False, True])
    async def test_toggle_is_hidden_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        sku: Sku,
        is_hidden: bool,
    ):
        request_data = ToggleIsHiddenRequest(
            sku_id=sku.id,
            is_hidden=is_hidden,
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/toggleIsHidden",
            content=payload_json,
        )
        assert response.status_code == 200, response.text

    async def test_move_to_not_found_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        item: Item,
    ):
        request_data = MoveToNotFoundRequest(
            id=item.id,
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/moveToNotFound",
            content=payload_json,
        )
        assert response.status_code == 200, response.text
