import uuid

from app.database import async_session_maker
from fastapi import APIRouter, Query
from schemas.acceptance import (
    CreateAcceptanceRequest,
    CreateAcceptanceResponse,
    GetAcceptanceInfoResponse,
)
from services.acceptance import AcceptanceService
from starlette import status

router = APIRouter(
    tags=["Acceptance"],
)


@router.get("/getAcceptanceInfo", response_model=GetAcceptanceInfoResponse)
async def get_acceptance_info(
    id: uuid.UUID = Query(),
) -> GetAcceptanceInfoResponse:
    """Получить инфо о приемке"""
    return await AcceptanceService(
        db_session_maker=async_session_maker,
    ).get_acceptance_info(id=id)


@router.post("/createAcceptance", response_model=CreateAcceptanceResponse, status_code=status.HTTP_201_CREATED)
async def create_acceptance(
    request_data: CreateAcceptanceRequest,
) -> CreateAcceptanceResponse:
    """Создать задачу на приемку товара"""
    # TODO: Добавить валидацию на пустые списки
    return await AcceptanceService(
        db_session_maker=async_session_maker,
    ).create_acceptance(request_data=request_data)
