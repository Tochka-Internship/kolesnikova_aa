import uuid
from abc import ABC, abstractmethod

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


class AbstractProvider(ABC):
    @abstractmethod
    async def add_one(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def find_all(self, *args, **kwargs):
        raise NotImplementedError


# TODO: Переписать так, чтобы не было выброса исключений?
class SQLAlchemyProvider(AbstractProvider):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict) -> uuid.UUID:
        stmt = insert(self.model).values(**data).returning(self.model.id)
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def edit_one(self, id: uuid.UUID, data: dict) -> uuid.UUID:
        stmt = update(self.model).values(**data).filter_by(id=id).returning(self.model.id)
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def find_all(self):
        stmt = select(self.model)
        res = await self.session.execute(stmt)
        res = [row[0].to_read_model() for row in res.all()]
        return res

    async def find_one(self, **filter_by):
        stmt = select(self.model).distinct().filter_by(**filter_by).options(joinedload('*'))
        res = await self.session.execute(stmt)
        res = res.unique().scalar_one()
        return res
