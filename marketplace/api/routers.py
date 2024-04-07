from api.acceptance import router as router_acceptance
from api.discount import router as router_discount
from api.posting import router as router_posting
from api.sku import router as router_sku
from api.task import router as router_task

all_routers = [
    router_posting,
    router_task,
    router_discount,
    router_sku,
    router_acceptance,
]
