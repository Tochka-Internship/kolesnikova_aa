from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.models.discount import DiscountFactory


async def test_discount_factory(db: AsyncSession):
    discount = DiscountFactory.build()
    assert discount
