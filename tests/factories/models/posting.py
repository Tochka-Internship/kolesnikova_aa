from datetime import UTC

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import Faker
from factory.fuzzy import FuzzyDecimal
from models import Posting, PostingStatus

from tests.conftest import TestDBSession


class PostingFactoryBase(AsyncSQLAlchemyFactory):
    class Meta:
        model = Posting
        sqlalchemy_session = TestDBSession
        sqlalchemy_session_persistence = 'commit'

    id = Faker('uuid4')
    status = Faker('random_element', elements=list(PostingStatus))
    created_at = Faker('date_time', tzinfo=UTC)
    cost = FuzzyDecimal(low=0, high=1000, precision=2)
