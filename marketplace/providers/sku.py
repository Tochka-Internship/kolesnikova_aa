from models import Sku
from utils.provider import SQLAlchemyProvider


class SkuProvider(SQLAlchemyProvider):
    model = Sku
