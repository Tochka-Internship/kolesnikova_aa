from collections.abc import Generator

from app.database import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> Generator[AsyncSession, None, None]:
    async with async_session_maker() as session:
        yield session
