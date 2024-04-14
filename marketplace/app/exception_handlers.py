from urllib.request import Request

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.exceptions import AppError, ValidationError, app_exc_from_http_exception


async def exception_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        # logger.error(f'Unhandled error: {exc!r}', exc_info=True)

        if not isinstance(exc, AppError):
            original_exc = exc
            exc = AppError(log=False)
            exc.__cause__ = original_exc

        return await app_error_handler(request, exc)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    # if exc.log:
    #     logger.error(repr(exc), exc_info=exc)

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(exc.get_data()),
        headers=exc.headers
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    exc: AppError = app_exc_from_http_exception(exc)
    return await app_error_handler(request, exc)


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    exc = ValidationError(detail=exc.errors())
    return await app_error_handler(request, exc)


EXCEPTION_HANDLERS = {
    AppError: app_error_handler,
    HTTPException: http_exception_handler,
    RequestValidationError: request_validation_exception_handler,
}


def setup_exception_handlers(app: FastAPI) -> None:
    for exc, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc, handler)

    # Использовать хендлер для кода 500 или Exception класса нельзя, тк в таком случае
    # request_id middleware будет пропущено при поднятии исключения.
    # Поэтому для отлова исключений используется свое middleware,
    # которое должно отрабатывать до request_id middleware.
    app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
