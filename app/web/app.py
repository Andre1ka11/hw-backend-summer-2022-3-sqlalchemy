from typing import Optional
from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from app.admin.models import AdminModel
from app.store import Store, setup_store
from app.store.database.database import Database
from app.web.config import Config, setup_config
from app.web.logger import setup_logging
from app.web.middlewares import setup_middlewares
from app.web.routes import setup_routes


class Application(AiohttpApplication):
    config: Optional[Config] = None
    store: Optional[Store] = None
    database: Optional[Database] = None


class Request(AiohttpRequest):
    admin: Optional[AdminModel] = None

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self) -> Database:
        return self.request.app.database

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})


app = Application()


async def on_startup(app: Application):
    await app.store.admins.connect(app)
    # Временно отключаем VK API
    # await app.store.vk_api.connect(app)


async def on_shutdown(app: Application):
    # Временно отключаем VK API
    # await app.store.vk_api.disconnect(app)
    await app.database.disconnect()


def setup_app(config_path: str) -> Application:
    setup_logging(app)
    setup_config(app, config_path)
    
    # Инициализируем database
    app.database = Database(app)
    
    session_setup(app, EncryptedCookieStorage(app.config.session.key))
    setup_routes(app)
    setup_aiohttp_apispec(
        app, title="Vk Quiz Bot", url="/docs/json", swagger_path="/docs"
    )
    setup_middlewares(app)
    setup_store(app)
    
    # Добавляем жизненный цикл
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    return app