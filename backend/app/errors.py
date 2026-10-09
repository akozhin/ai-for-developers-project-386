"""Единый формат ошибок API: `{code, message}` и `422` со списком полей (см. контракт)."""

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match

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


def _field_name(error: Mapping[str, Any]) -> str:
    """Имя поля из ошибки Pydantic; нечитаемый JSON относится к телу целиком."""
    if error["type"] == "json_invalid":
        return "body"
    return ".".join(str(part) for part in error["loc"][1:]) or "body"


async def _handle_validation_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):  # pragma: no cover
        raise exc
    fields = [
        {
            "field": _field_name(error),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return _validation_response(fields)


_PROBED_METHODS = ("DELETE", "GET", "HEAD", "PATCH", "POST", "PUT")


def _allowed_methods(request: Request) -> str:
    """Методы, которые принимает путь (Starlette в `Allow` берёт только первый маршрут)."""
    allowed = [
        method
        for method in _PROBED_METHODS
        if any(
            route.matches({**request.scope, "method": method})[0] == Match.FULL
            for route in request.app.router.routes
        )
    ]
    return ", ".join(allowed)


def _validation_response(fields: list[dict[str, str]]) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={"code": "validation_error", "message": "Ошибка валидации", "fields": fields},
    )


async def _handle_http_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):  # pragma: no cover
        raise exc
    if exc.status_code == HTTPStatus.BAD_REQUEST:
        # Тело нельзя прочитать вовсе (например, не UTF-8): для контракта это ошибка валидации.
        return _validation_response([{"field": "body", "message": "Некорректное тело запроса"}])
    headers = dict(exc.headers or {})
    if exc.status_code == HTTPStatus.METHOD_NOT_ALLOWED:
        headers["Allow"] = _allowed_methods(request)
    code, message = _HTTP_ERRORS.get(
        exc.status_code,
        (f"http_{exc.status_code}", "Ошибка запроса"),
    )
    return _error_response(exc.status_code, code, message, headers)


async def _handle_unexpected_error(_: Request, __: Exception) -> JSONResponse:
    return _error_response(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "Внутренняя ошибка")


def register_error_handlers(application: FastAPI) -> None:
    """Подключить обработчики, приводящие все ошибки к формату контракта."""
    application.add_exception_handler(ApiError, _handle_api_error)
    application.add_exception_handler(RequestValidationError, _handle_validation_error)
    application.add_exception_handler(StarletteHTTPException, _handle_http_error)
    application.add_exception_handler(Exception, _handle_unexpected_error)
