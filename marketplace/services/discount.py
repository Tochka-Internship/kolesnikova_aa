import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.database import async_session_maker
from models import Discount, DiscountStatus, Sku
from providers.discount import DiscountProvider
from providers.sku import SkuProvider
from service_models import CreateDiscountDTO, DiscountDTO
from services.sku import SkuService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class DiscountService:
    db_session_maker: Callable[[], AsyncSession]
    discount_provider: Callable[[AsyncSession], DiscountProvider] = DiscountProvider
    sku_provider: Callable[[AsyncSession], SkuProvider] = SkuProvider
    sku_service: Callable[[AsyncSession], SkuService] = SkuService

    async def get_discount(self, discount_id: uuid.UUID) -> DiscountDTO:
        async with self.db_session_maker() as session:
            # TODO: Нужно обрабатывать случаи отсутствия записи
            discount: Discount = await self.discount_provider(session).find_one(id=discount_id)
            return discount.as_dto()

    async def cancel_discount(self, discount_id: uuid.UUID) -> uuid.UUID:
        async with self.db_session_maker() as session:
            discount_id: uuid.UUID = await self.discount_provider(session).edit_one(
                id=discount_id,
                data={'status': DiscountStatus.FINISHED}
            )
            await session.commit()
        return discount_id

    async def create_discount(self, discount_data: CreateDiscountDTO) -> uuid.UUID:
        async with self.db_session_maker() as session:
            discount = Discount(
                status=DiscountStatus.ACTIVE,
                percentage=discount_data.percentage,
            )
            session.add(discount)
            skus_query = (
                select(Sku)
                .filter(Sku.id.in_(discount_data.sku_ids))
            )
            skus: Sequence[Sku] = (await session.execute(skus_query)).scalars().all()
            discount.skus = skus
            await session.commit()
            # TODO: Добавить в фоновые задачи
            # NOTE: Очень важно передать НЕ текущую сессию, иначе будет либо ожидание, либо сессия будет уже закрыта
            # await SkuService(
            await self.sku_service(
                db_session_maker=async_session_maker,
            ).update_skus_actual_prices(sku_ids=[sku.id for sku in skus])
        return discount.id
