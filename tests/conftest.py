import asyncio
import os

import pytest
from app.fastapi import create_app
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session
from sqlalchemy.orm import sessionmaker

# from marketplace.app.config import config
from marketplace.app.database import Base, async_session_maker, engine


def scopefunc():
    # Получение текущего теста
    return os.environ.get('PYTEST_CURRENT_TEST').rsplit(' ', 1)[0]


# Для использования с фабриками
# Не забывать использовать фикстуру db, иначе будут ошибки
TestDBSession = async_scoped_session(
    session_factory=sessionmaker(
        class_=AsyncSession,
        autoflush=True,
        autocommit=False,
        expire_on_commit=False,
    ),
    scopefunc=scopefunc,
)


# TestDBSession = scoped_session(async_session_maker)


def pytest_collection_modifyitems(items):
    for item in items:
        if asyncio.iscoroutinefunction(item.obj):
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def app():
    app = create_app()
    # yield app
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(app) -> AsyncClient:
    headers = {}
    async with AsyncClient(app=app, base_url='http://test', headers=headers) as ac:
        yield ac


@pytest.fixture()
async def db() -> AsyncSession:
    async with engine.connect() as conn:
        TestDBSession.configure(bind=conn)
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

        async with async_session_maker() as session:
            yield session

        await conn.run_sync(Base.metadata.drop_all)
        await conn.commit()
