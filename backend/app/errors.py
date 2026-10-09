"""Единый формат ошибок API: `{code, message}` и `422` со списком полей (см. контракт)."""

from collections.abc import Mapping
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_HTTP_ERRORS: dict[int, tuple[str, str]] = {
    HTTPStatus.NOT_FOUND: ("not_found", "Ресурс не найден"),
    HTTPStatus.METHOD_NOT_ALLOWED: ("method_not_allowed", "Метод не поддерживается"),
}


class ApiError(Exception):
    """Ожидаемая ошибка API с кодом из контракта."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        """Запомнить HTTP-статус, машинный код и сообщение для гостя."""
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _error_response(
    status_code: int,
    code: str,
    message: str,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
        headers=headers,
    )


async def _handle_api_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ApiError):  # pragma: no cover - защита от неверной регистрации
        raise exc
    return _error_response(exc.status_code, exc.code, exc.message)


async def _handle_validation_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):  # pragma: no cover
        raise exc
    fields = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or "body",
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={"code": "validation_error", "message": "Ошибка валидации", "fields": fields},
    )


async def _handle_http_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):  # pragma: no cover
        raise exc
    code, message = _HTTP_ERRORS.get(
        exc.status_code,
        (f"http_{exc.status_code}", "Ошибка запроса"),
    )
    return _error_response(exc.status_code, code, message, exc.headers)


async def _handle_unexpected_error(_: Request, __: Exception) -> JSONResponse:
    return _error_response(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "Внутренняя ошибка")


def register_error_handlers(application: FastAPI) -> None:
    """Подключить обработчики, приводящие все ошибки к формату контракта."""
    application.add_exception_handler(ApiError, _handle_api_error)
    application.add_exception_handler(RequestValidationError, _handle_validation_error)
    application.add_exception_handler(StarletteHTTPException, _handle_http_error)
    application.add_exception_handler(Exception, _handle_unexpected_error)
