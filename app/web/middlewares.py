import json
import typing

from aiohttp.web_exceptions import (
    HTTPException, 
    HTTPUnprocessableEntity, 
    HTTPUnauthorized,
    HTTPForbidden
)
from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware
from aiohttp_session import get_session
from marshmallow import ValidationError

from app.web.utils import error_json_response

if typing.TYPE_CHECKING:
    from app.web.app import Application, Request


HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "not_implemented",
    409: "conflict",
    500: "internal_server_error",
}


@middleware
async def auth_middleware(request: "Request", handler):
    """Проверка авторизации для защищенных маршрутов"""
    # Пропускаем маршруты, не требующие авторизации
    if request.path == "/admin.login" and request.method == "POST":
        return await handler(request)
    
    try:
        # Получаем сессию
        session = await get_session(request)
        admin_id = session.get("admin_id")
        
        if not admin_id:
            return error_json_response(
                http_status=401,
                status=HTTP_ERROR_CODES[401],
                message="Unauthorized",
                data={},
            )
        
        # Получаем админа из базы
        admin = await request.app.store.admins.get_by_id(admin_id)
        
        if not admin:
            return error_json_response(
                http_status=403,
                status=HTTP_ERROR_CODES[403],
                message="Forbidden",
                data={},
            )
        
        # Добавляем админа в request
        request.admin = admin
    except Exception:
        return error_json_response(
            http_status=401,
            status=HTTP_ERROR_CODES[401],
            message="Unauthorized",
            data={},
        )
    
    return await handler(request)


@middleware
async def error_handling_middleware(request: "Request", handler):
    try:
        response = await handler(request)
        return response
    except HTTPUnprocessableEntity as e:
        # Для ошибок валидации marshmallow
        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message=e.reason,
            data={"json": json.loads(e.text)},
        )
    except ValidationError as e:
        # Для наших кастомных ValidationError
        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message="Validation error",
            data={"json": e.messages if hasattr(e, 'messages') else str(e)},
        )
    except HTTPUnauthorized as e:
        return error_json_response(
            http_status=401,
            status=HTTP_ERROR_CODES[401],
            message="Unauthorized",
            data={},
        )
    except HTTPForbidden as e:
        return error_json_response(
            http_status=403,
            status=HTTP_ERROR_CODES[403],
            message="Forbidden",
            data={},
        )
    except HTTPException as e:
        return error_json_response(
            http_status=e.status,
            status=HTTP_ERROR_CODES.get(e.status, "unknown"),
            message=str(e),
            data={},
        )
    except Exception as e:
        request.app.logger.error("Exception", exc_info=e)
        return error_json_response(
            http_status=500, 
            status=HTTP_ERROR_CODES[500],
            message="Internal server error",
            data={},
        )


def setup_middlewares(app: "Application"):
    # Важен порядок: auth должен быть первым
    app.middlewares.append(auth_middleware)
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(validation_middleware)