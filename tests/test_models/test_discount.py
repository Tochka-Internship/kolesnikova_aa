import uuid
from datetime import UTC, datetime

from models import Discount, DiscountStatus
from sqlalchemy.ext.asyncio import AsyncSession


async def test_discount_creation(db: AsyncSession):
    discount = Discount(
        id=uuid.uuid4(),
        status=DiscountStatus.ACTIVE,
        created_at=datetime.now(tz=UTC),
        percentage=10,
    )
    assert discount
