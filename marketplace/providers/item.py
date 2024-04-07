from models import Item
from utils.provider import SQLAlchemyProvider


class ItemProvider(SQLAlchemyProvider):
    model = Item
