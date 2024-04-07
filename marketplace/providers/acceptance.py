from models import Acceptance
from utils.provider import SQLAlchemyProvider


class AcceptanceProvider(SQLAlchemyProvider):
    model = Acceptance
