from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.models.discount import DiscountFactoryBase


async def test_discount_factory(db: AsyncSession):
    discount = DiscountFactoryBase.build()
    assert discount
