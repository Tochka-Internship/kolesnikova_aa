from datetime import UTC

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import Faker
from factory.fuzzy import FuzzyDecimal
from models import Sku

from tests.conftest import TestDBSession


# class SkuFactory(SQLAlchemyModelFactory):
class SkuFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = Sku
        sqlalchemy_session = TestDBSession
        sqlalchemy_session_persistence = 'commit'

    id = Faker('uuid4')
    created_at = Faker('date_time', tzinfo=UTC)
    # https://stackoverflow.com/a/72909669/24065830
    actual_price = FuzzyDecimal(low=0, high=1000, precision=2)
    base_price = FuzzyDecimal(low=0, high=1000, precision=2)
    count = Faker('pyint', min_value=0, max_value=1000)
    is_hidden = Faker('pybool')
