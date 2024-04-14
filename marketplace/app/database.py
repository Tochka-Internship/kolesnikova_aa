from typing import Annotated

from sqlalchemy import String, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import ColumnProperty, DeclarativeBase

from app.config import config

engine = create_async_engine(
    url=str(config.DATABASE_URI),
    echo=True,
    # TODO: asyncpg не принимает "options" - уточнить замену
    # connect_args={
    #     # https://stackoverflow.com/a/59932909
    #     "options": "-c timezone=utc",
    # }
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

str_256 = Annotated[str, 256]


class Base(DeclarativeBase):
    type_annotation_map = {
        str_256: String(256)
    }

    __repr_fields__ = ('id',)

    def to_dict(self):
        model = self
        fields_prop = {
            key: getattr(model, key)
            for key, value in inspect(model).mapper.all_orm_descriptors.items()
            if not hasattr(value, 'original_property') and hasattr(value, 'prop') and isinstance(
                value.prop, (ColumnProperty,))
        }

        return fields_prop


async def get_async_session():
    async with async_session_maker() as session:
        yield session
