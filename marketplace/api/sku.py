import uuid
from typing import Any

from app.database import async_session_maker
from fastapi import APIRouter, Query
from providers.sku import SkuProvider
from schemas.sku import (
    GetItemInfoBySkuIdResponse,
    GetItemInfoResponse,
    GetSkuInfoResponse,
    MarkdownItemRequest,
    MoveToNotFoundRequest,
    SetSkuPriceRequest,
    ToggleIsHiddenRequest,
)
from services.sku import SkuService
from starlette import status

router = APIRouter(
    tags=["Sku"],
)


@router.get("/getItemInfo", response_model=GetItemInfoResponse)
async def get_item_info(
    id: uuid.UUID = Query(),
) -> GetItemInfoResponse:
    """Получение инфо о конкретной копии товара"""
    return await SkuService(
        db_session_maker=async_session_maker,
        sku_provider=SkuProvider,
    ).get_item_info(item_id=id)


@router.get("/getSkuInfo", response_model=GetSkuInfoResponse)
async def get_sku_info(
    id: uuid.UUID = Query(),
) -> GetSkuInfoResponse:
    """Получение инфо о товарной группе"""
    return await SkuService(
        db_session_maker=async_session_maker,
        sku_provider=SkuProvider,
    ).get_sku_info(sku_id=id)


@router.get("/getItemInfoBySkuId", response_model=GetItemInfoBySkuIdResponse)
async def get_item_info_by_sku_id(
    id: uuid.UUID = Query(),
) -> GetItemInfoBySkuIdResponse:
    """Получение всех копий товаров с одинаковым SKU"""
    return await SkuService(
        db_session_maker=async_session_maker,
        sku_provider=SkuProvider,
    ).get_item_info_by_sku_id(sku_id=id)


@router.post("/markdownItem", status_code=status.HTTP_200_OK)
async def markdown_item(
    request_data: MarkdownItemRequest,
) -> Any:
    """Уценить товар"""
    await SkuService(
        db_session_maker=async_session_maker,
        sku_provider=SkuProvider,
    ).markdown_item(request_data=request_data)
    return status.HTTP_200_OK


@router.post("/setSkuPrice", status_code=status.HTTP_200_OK)
async def set_sku_price(
    request_data: SetSkuPriceRequest,
) -> Any:
    """Изменить базовую стоимость товара"""
    await SkuService(
        db_session_maker=async_session_maker,
        sku_provider=SkuProvider,
    ).set_sku_price(request_data=request_data)
    return status.HTTP_200_OK


@router.post("/toggleIsHidden", status_code=status.HTTP_200_OK)
async def toggle_is_hidden(
    request_data: ToggleIsHiddenRequest,
) -> Any:
    """Скрыть или отобразить товар для покупки"""
    await SkuService(
        db_session_maker=async_session_maker,
        sku_provider=SkuProvider,
    ).toggle_is_hidden(request_data=request_data)
    return status.HTTP_200_OK


@router.post("/moveToNotFound", status_code=status.HTTP_200_OK)
async def move_to_not_found(
    request_data: MoveToNotFoundRequest,
) -> Any:
    """Подвинуть товар на сток NotFound"""
    await SkuService(
        db_session_maker=async_session_maker,
        sku_provider=SkuProvider,
    ).move_to_not_found(request_data=request_data)
    return status.HTTP_200_OK
