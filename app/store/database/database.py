from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import URL

from app.store.database.sqlalchemy_base import BaseModel

if TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application") -> None:
        self.app = app
        self.engine: Optional[AsyncEngine] = None
        self._db: type[DeclarativeBase] = BaseModel
        self.session: Optional[async_sessionmaker[AsyncSession]] = None

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        # Создаем URL для подключения к БД
        db_config = self.app.config.database
        url = URL.create(
            drivername="postgresql+asyncpg",
            username=db_config.user,
            password=db_config.password,
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
        )
        
        # Создаем движок
        self.engine = create_async_engine(url, echo=True)
        
        # Создаем фабрику сессий
        self.session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Создаем таблицы
        async with self.engine.begin() as conn:
            await conn.run_sync(self._db.metadata.create_all)

    async def disconnect(self, *args: Any, **kwargs: Any) -> None:
        if self.engine:
            await self.engine.dispose()