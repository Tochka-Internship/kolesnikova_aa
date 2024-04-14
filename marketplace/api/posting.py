import uuid
from typing import Any

from api.dependencies import get_db
from fastapi import APIRouter, Depends, Query
from schemas.posting import (
    CancelPostingRequest,
    CreatePostingRequest,
    CreatePostingResponse,
    GetPostingResponse,
)
from services.posting import PostingService
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

router = APIRouter(
    tags=["Posting"],
)


@router.get("/getPosting", response_model=GetPostingResponse)
async def get_posting(
    id: uuid.UUID = Query(),
    db: AsyncSession = Depends(get_db),
) -> GetPostingResponse:
    """Получение информации по заказу"""
    return await PostingService(
        db_session_maker=lambda: db,
    ).get_posting(posting_id=id)


@router.post("/createPosting", response_model=CreatePostingResponse)
async def create_posting(
    request_data: CreatePostingRequest,
    db: AsyncSession = Depends(get_db),
) -> CreatePostingResponse:
    """Создание заказа"""
    return await PostingService(
        db_session_maker=lambda: db,
    ).create_posting(request_data=request_data)


@router.post("/cancelPosting", status_code=status.HTTP_200_OK)
async def cancel_posting(
    request_data: CancelPostingRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Отмена заказа"""
    await PostingService(
        db_session_maker=lambda: db,
    ).cancel_posting(request_data=request_data)
    return status.HTTP_200_OK
