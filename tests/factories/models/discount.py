from datetime import UTC

from factory import Faker
from factory.alchemy import SQLAlchemyModelFactory
from models import Discount, DiscountStatus

from tests.conftest import TestDBSession


# class DiscountFactory(AsyncSQLAlchemyFactory):
# class DiscountFactory(Factory):
class DiscountFactory(SQLAlchemyModelFactory):
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
