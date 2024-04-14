from models import Posting
from utils.provider import SQLAlchemyProvider


class PostingProvider(SQLAlchemyProvider):
    model = Posting
