from datetime import UTC

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import Faker
from models import Acceptance

from tests.conftest import TestDBSession


class AcceptanceFactoryBase(AsyncSQLAlchemyFactory):
    class Meta:
        model = Acceptance
        sqlalchemy_session = TestDBSession
        sqlalchemy_session_persistence = 'commit'

    id = Faker('uuid4')
    created_at = Faker('date_time', tzinfo=UTC)
