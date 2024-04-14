from models import Discount
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from utils.provider import SQLAlchemyProvider


class DiscountProvider(SQLAlchemyProvider):
    model = Discount

    async def find_one(self, **filter_by) -> Discount:
        stmt = select(self.model).filter_by(**filter_by).options(
            joinedload(self.model.skus)
        )
        # from app.database import engine
        # str(stmt.compile(engine, compile_kwargs={"literal_binds": True}))
        res = await self.session.execute(stmt)
        res = res.unique().scalar_one()
        return res
