import enum
from dataclasses import asdict, dataclass
from http import HTTPStatus
from typing import Any

from starlette.exceptions import HTTPException
from utils.utils import remove_empty_keys


class ErrorCodes(enum.Enum):
    # Ошибка валидации параметров запрос. Данный код используется при ошибках анализа запроса,
    # например, отсутствуют обязательные параметры, переданы параметры не того типа.
    EX_VALIDATION_ERROR = 'EX_VALIDATION_ERROR'
    # Неизвестная ошибка. Все остальные ошибки, не имеющие отдельного обработчика
    EX_UNKNOWN_ERROR = 'EX_UNKNOWN_ERROR'

    EX_NOT_FOUND = 'EX_NOT_FOUND'
    EX_FORBIDDEN = 'EX_FORBIDDEN'


@dataclass
class AppError(Exception):
    # HTTP код ответа
    status_code: int = 500
    # Текстовый код ошибки
    error: str = ErrorCodes.EX_UNKNOWN_ERROR.value
    # Машиночитаемая дополнительная информация об ошибке,
    # например структура с детальной информацией об ошибках валидации от pydantic
    detail: Any | None = None
    # Текстовое сообщение об ошибке
    message: str | None = None
    # Заголовки ответа, добавлено для совместимости с fastapi.HTTPException
    headers: dict[str, str] | None = None
    # Нужно ли логировать ошибку.
    log: bool = True

    def get_data(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop('status_code', None)
        data.pop('headers', None)
        data.pop('log', None)
        if self.__cause__:
            data['reason'] = repr(self.__cause__)

        return data


@dataclass
class ExternalSystemError(AppError):
    """
    Base class to create any 'System' error,
    which means remote system is unavailable or
    any unhandled error has occured
    """
    status_code: int = 500


@dataclass
class ExternalBusinessError(AppError):
    """
    Base class to create any 'Business' error,
    which means remote system cannot process request
    because of provided data is invalid, violate consistency, etc
    """
    status_code: int = 400


@dataclass
class ValidationError(ExternalBusinessError):
    status_code: int = 400
    error: str = ErrorCodes.EX_VALIDATION_ERROR.value
    message: str | None = 'Bad request.'


@dataclass
class ValidationError(ExternalBusinessError):
    status_code: int = 400
    error: str = ErrorCodes.EX_VALIDATION_ERROR.value
    message: str | None = 'Bad request.'


@dataclass
class ForbiddenError(ExternalBusinessError):
    status_code: int = 403
    error: str = ErrorCodes.EX_FORBIDDEN.value
    message: str | None = 'You do not have permission to perform this action.'


@dataclass
class NotFoundError(ExternalBusinessError):
    status_code: int = 404
    error: str = ErrorCodes.EX_NOT_FOUND.value
    message: str | None = 'Object not found.'


@dataclass
class MethodNotAllowedError(ExternalBusinessError):
    status_code: int = 405
    error: str = ErrorCodes.EX_VALIDATION_ERROR.value
    message: str | None = 'Method not allowed.'


_CODE_TO_CLASS_MAP = {
    **{422: ValidationError},
    **{
        cls.status_code: cls
        for cls in [ValidationError, ForbiddenError, NotFoundError, MethodNotAllowedError]
    }
}


def app_exc_from_http_exception(exc: HTTPException) -> AppError:
    cls: type[AppError] = _CODE_TO_CLASS_MAP.get(exc.status_code, AppError)
    exc_data = remove_empty_keys({
        'headers': getattr(exc, 'headers', None),
        'detail': exc.detail
    })
    if 400 <= exc.status_code <= 499 and cls is AppError:
        exc_data['status_code'] = exc.status_code
        try:
            status = HTTPStatus(exc.status_code)
            exc_data['message'] = status.description
        except ValueError:
            pass

    # В случае если нет обработчика для запроса fastapi поднимает HTTPException(status_code=404)
    # Надежного способа поймать именно эту ситуацию нет.
    if exc.status_code == 404 and exc.detail == HTTPStatus.NOT_FOUND.phrase:
        exc_data['message'] = 'No such route.'

    result = cls(**exc_data)
    result.__cause__ = exc.__cause__
    return result
