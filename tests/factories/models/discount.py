from datetime import UTC

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import Faker
from models import Discount, DiscountStatus

from tests.conftest import TestDBSession


class DiscountFactoryBase(AsyncSQLAlchemyFactory):
    class Meta:
        model = Discount
        sqlalchemy_session = TestDBSession
        sqlalchemy_session_persistence = 'commit'

    id = Faker('uuid4')
    status = Faker(
        'random_element',
        elements=list(DiscountStatus),
    )
    created_at = Faker('date_time', tzinfo=UTC)
    percentage = Faker('pyint')
