import uuid

from api.dependencies import get_db
from fastapi import APIRouter, Depends, Query
from schemas.acceptance import (
    CreateAcceptanceRequest,
    CreateAcceptanceResponse,
    GetAcceptanceInfoResponse,
)
from services.acceptance import AcceptanceService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    tags=["Acceptance"],
)


@router.get("/getAcceptanceInfo", response_model=GetAcceptanceInfoResponse)
async def get_acceptance_info(
    id: uuid.UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> GetAcceptanceInfoResponse:
    """Получить инфо о приемке"""
    return await AcceptanceService(
        db_session_maker=lambda: db,
    ).get_acceptance_info(id=id)


@router.post("/createAcceptance", response_model=CreateAcceptanceResponse)
async def create_acceptance(
    request_data: CreateAcceptanceRequest,
    db: AsyncSession = Depends(get_db),
) -> CreateAcceptanceResponse:
    """Создать задачу на приемку товара"""
    # TODO: Добавить валидацию на пустые списки
    return await AcceptanceService(
        db_session_maker=lambda: db,
    ).create_acceptance(request_data=request_data)
