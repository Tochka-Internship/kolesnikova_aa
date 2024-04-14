from factory import Factory, Faker, List, SubFactory
from schemas.acceptance import (
    AcceptanceInfoSkuByStockStatus,
    CreateAcceptanceRequest,
    StockStatusSchema,
)


class AcceptanceInfoSkuByStockStatusFactory(Factory):
    class Meta:
        model = AcceptanceInfoSkuByStockStatus

    sku_id = Faker('uuid4')
    stock = Faker(
        'random_element',
        elements=list(StockStatusSchema),
    )
    count = Faker('pyint', min_value=0, max_value=10)


class CreateAcceptanceRequestFactory(Factory):
    class Meta:
        model = CreateAcceptanceRequest

    items_to_accept = List([SubFactory(AcceptanceInfoSkuByStockStatusFactory)])
