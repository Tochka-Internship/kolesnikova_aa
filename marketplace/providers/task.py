from models import Task
from utils.provider import SQLAlchemyProvider


class TaskProvider(SQLAlchemyProvider):
    model = Task
