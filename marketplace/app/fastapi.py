from fastapi import FastAPI
from sqlalchemy.orm import configure_mappers

from app.exception_handlers import setup_exception_handlers
from marketplace.api.routers import all_routers


def create_app() -> FastAPI:
    app = FastAPI(
        title="Универмаг 2.0",
        openapi_url="/openapi.json",
    )
    # Порядок регистрации middleware важен
    setup_exception_handlers(app)

    for router in all_routers:
        app.include_router(router)

    _configure_db()

    return app


def _configure_db():
    configure_mappers()
