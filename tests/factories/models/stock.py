from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import Faker
from models import Stock, StockStatus

from tests.conftest import TestDBSession


class StockFactoryBase(AsyncSQLAlchemyFactory):
    class Meta:
        model = Stock
        sqlalchemy_session = TestDBSession
        sqlalchemy_session_persistence = 'commit'

    id = Faker('uuid4')
    status = Faker('random_element', elements=list(StockStatus))
    is_reserved = Faker('pybool')
