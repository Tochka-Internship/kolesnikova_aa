import uuid
from typing import Any

from app.database import async_session_maker
from fastapi import APIRouter, Query
from schemas.posting import (
    CancelPostingRequest,
    CreatePostingRequest,
    CreatePostingResponse,
    GetPostingResponse,
)
from services.posting import PostingService
from starlette import status

router = APIRouter(
    tags=["Posting"],
)


@router.get("/getPosting", response_model=GetPostingResponse)
async def get_posting(
    id: uuid.UUID = Query(),
) -> GetPostingResponse:
    """Получение информации по заказу"""
    return await PostingService(
        db_session_maker=async_session_maker,
    ).get_posting(posting_id=id)


@router.post("/createPosting", response_model=CreatePostingResponse, status_code=status.HTTP_201_CREATED)
async def create_posting(
    request_data: CreatePostingRequest,
) -> CreatePostingResponse:
    """Создание заказа"""
    return await PostingService(
        db_session_maker=async_session_maker,
    ).create_posting(request_data=request_data)


@router.post("/cancelPosting", status_code=status.HTTP_200_OK)
async def cancel_posting(
    request_data: CancelPostingRequest,
) -> Any:
    """Отмена заказа"""
    await PostingService(
        db_session_maker=async_session_maker,
    ).cancel_posting(request_data=request_data)
    return status.HTTP_200_OK
