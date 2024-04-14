from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import Faker
from models import ItemDiscount, ItemDiscountType

from tests.conftest import TestDBSession


class ItemDiscountFactoryBase(AsyncSQLAlchemyFactory):
    class Meta:
        model = ItemDiscount
        sqlalchemy_session = TestDBSession
        sqlalchemy_session_persistence = 'commit'

    id = Faker('uuid4')
    type = Faker('random_element', elements=list(ItemDiscountType))
    percentage = Faker('pyint', min_value=1, max_value=99)
