from datetime import UTC

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import Faker
from models import Task, TaskStatus, TaskType

from tests.conftest import TestDBSession


class TaskFactoryBase(AsyncSQLAlchemyFactory):
    class Meta:
        model = Task
        sqlalchemy_session = TestDBSession
        sqlalchemy_session_persistence = 'commit'

    id = Faker('uuid4')
    status = Faker('random_element', elements=list(TaskStatus))
    created_at = Faker('date_time', tzinfo=UTC)
    type = Faker('random_element', elements=list(TaskType))
