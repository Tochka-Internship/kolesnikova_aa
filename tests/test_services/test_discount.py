import uuid

import pytest
from app.database import async_session_maker
from models import Discount, DiscountStatus
from providers.discount import DiscountProvider
from services.discount import DiscountService
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.models.discount import DiscountFactoryBase


class TestDiscountService:
    @pytest.fixture()
    async def service(self, db: AsyncSession) -> DiscountService:
        return DiscountService(
            # db_session_maker=lambda: db,
            db_session_maker=async_session_maker,
            discount_provider=DiscountProvider
        )

    @pytest.fixture
    async def discount(self, db: AsyncSession) -> Discount:
        return await DiscountFactoryBase.create(skus=[])

    @pytest.fixture
    async def active_discount(self, db: AsyncSession) -> Discount:
        return await DiscountFactoryBase.create(status=DiscountStatus.ACTIVE)

    async def test_get_discount_success(
        self,
        db: AsyncSession,
        service: DiscountService,
        discount: Discount,
    ):
        """Проверка отработки сценария при наличии дискаунта"""
        returned_discount_dto = await service.get_discount(discount_id=discount.id)
        assert returned_discount_dto == discount.as_dto()

    async def test_get_discount_not_found(
        self,
        db: AsyncSession,
        service: DiscountService,
    ):
        """Проверка отработки сценария при отсутствии дискаунта"""
        with pytest.raises(NoResultFound) as exc:
            await service.get_discount(discount_id=uuid.uuid4())
        assert exc

    # TODO: Написать тест на отмену неактивного дискаунта
    async def test_cancel_discount_success(
        self,
        db: AsyncSession,
        service: DiscountService,
        active_discount: Discount,
        # discount_repository: DiscountRepository,
    ):
        """Проверка успешной отмены активного дискаунта"""
        assert active_discount.status != DiscountStatus.FINISHED
        returned_discount_id = await service.cancel_discount(discount_id=active_discount.id)
        changed_discount = await DiscountProvider(db).find_one(id=returned_discount_id)

        assert changed_discount.status is DiscountStatus.FINISHED
