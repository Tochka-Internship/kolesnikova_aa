from decimal import Decimal

from httpx import AsyncClient
from models import Sku
from sqlalchemy.ext.asyncio import AsyncSession


class TestSkuApi:
    # @pytest.fixture
    # async def sku(self, db: AsyncSession) -> Sku:
    #     _sku = SkuFactory.build(
    #         # discount=None,
    #         # items=None,
    #     )
    #     # _sku = SkuFactory()
    #     db.add(_sku)
    #     await db.commit()
    #     return _sku

    async def test_get_item_info_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        # sku: Sku,
    ):
        # db.add(sku)
        # await db.commit()
        # sku = SkuFactory.build(
        #     # discount=None,
        #     # items=None,
        # )
        # sku = await SkuFactory.create()
        # _sku = SkuFactory()
        sku = Sku(
            # id
            # created_at
            actual_price=Decimal("0.00"),
            base_price=Decimal("0.00"),
            count=1000,
            is_hidden=False,
        )
        db.add(sku)
        await db.commit()
        # TODO: Что-то не так с сессией БД
        response = await client.get(
            url="/getItemInfo",
            params={"id": sku.id},
        )
        assert response.status_code == 200, response.text
