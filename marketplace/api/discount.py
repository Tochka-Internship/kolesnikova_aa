import uuid

from api.dependencies import get_db
from fastapi import APIRouter, Depends, Query
from providers.discount import DiscountProvider
from schemas.discount import (
    CancelDiscountSchema,
    CreateDiscountResponseSchema,
    CreateDiscountSchema,
    DiscountSchema,
)
from service_models import CreateDiscountDTO
from services.discount import DiscountService
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

router = APIRouter(
    tags=["Discount"],
)


@router.get("/getDiscount", response_model=DiscountSchema)
async def get_discount(
    id: uuid.UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> DiscountSchema:
    """Получение инфо об акции"""
    discount_dto = await DiscountService(
        db_session_maker=lambda: db,
        discount_provider=DiscountProvider,
    ).get_discount(discount_id=id)
    return DiscountSchema(
        id=discount_dto.id,
        status=discount_dto.status,
        created_at=discount_dto.created_at,
        percentage=discount_dto.percentage,
        sku_ids=[sku.id for sku in discount_dto.skus],
    )


@router.post("/createDiscount", response_model=CreateDiscountResponseSchema)
async def create_discount(
    request_data: CreateDiscountSchema,
    db: AsyncSession = Depends(get_db),
) -> CreateDiscountResponseSchema:
    """Создание акции"""
    discount_id = await DiscountService(
        db_session_maker=lambda: db,
        discount_provider=DiscountProvider,
    ).create_discount(
        discount_data=CreateDiscountDTO(
            sku_ids=request_data.sku_ids,
            percentage=request_data.percentage,
        )
    )
    return CreateDiscountResponseSchema(id=discount_id)


@router.post("/cancelDiscount", status_code=status.HTTP_200_OK)
async def cancel_discount(
    request_data: CancelDiscountSchema,
    db: AsyncSession = Depends(get_db),
):
    """Закончить акцию"""
    await DiscountService(
        db_session_maker=lambda: db,
        discount_provider=DiscountProvider,
    ).cancel_discount(discount_id=request_data.id)
    return status.HTTP_200_OK
