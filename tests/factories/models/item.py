from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import Faker
from models import Item

from tests.conftest import TestDBSession


class ItemFactoryBase(AsyncSQLAlchemyFactory):
    class Meta:
        model = Item
        sqlalchemy_session = TestDBSession
        sqlalchemy_session_persistence = 'commit'

    id = Faker('uuid4')
