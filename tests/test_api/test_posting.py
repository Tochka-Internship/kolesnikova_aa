import pytest
from factories.models.posting import PostingFactoryBase
from factories.schemas.posting import CreatePostingRequestFactory, OrderedGoodFactory
from httpx import AsyncClient
from models import Posting, PostingStatus
from schemas.posting import (
    CancelPostingRequest,
    CreatePostingRequest,
    GetPostingResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession


class TestPostingApi:
    @pytest.fixture
    async def posting(self, db: AsyncSession) -> Posting:
        return await PostingFactoryBase.create(
            status=PostingStatus.IN_ITEM_PICK,
        )

    async def test_get_posting_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        posting: Posting,
    ):
        response = await client.get(
            url="/getPosting",
            params={"id": posting.id},
        )
        assert response.status_code == 200, response.text
        assert GetPostingResponse(**response.json())

    @pytest.mark.parametrize("skus_count", [1, 5, 10])
    @pytest.mark.parametrize("items_count_per_type_per_sku", [1, 5, 10])
    async def test_create_posting_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        skus_count,
        items_count_per_type_per_sku,
    ):
        # TODO: Проверить количество создаваемых записей
        # TODO: Написать тест на нулевое количество
        request_data: CreatePostingRequest = CreatePostingRequestFactory(
            items_to_accept=OrderedGoodFactory.build_batch(
                size=skus_count,
                valid_ids_count=items_count_per_type_per_sku,
                defect_ids_count=items_count_per_type_per_sku,
            ),
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/createPosting",
            content=payload_json,
        )
        assert response.status_code == 201, response.text

    async def test_cancel_posting_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        posting: Posting,
    ):
        request_data = CancelPostingRequest(
            id=posting.id,
        )
        payload_json = request_data.json(by_alias=True)

        response = await client.post(
            url="/cancelPosting",
            content=payload_json,
        )
        assert response.status_code == 200, response.text
