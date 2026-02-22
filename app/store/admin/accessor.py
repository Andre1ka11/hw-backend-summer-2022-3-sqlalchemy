from hashlib import sha256
from typing import TYPE_CHECKING, Optional

from app.admin.models import AdminModel
from app.base.base_accessor import BaseAccessor

if TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application") -> None:
        # Создаем админа из конфига при запуске
        await self.create_admin(
            email=app.config.admin.email,
            password=app.config.admin.password,
        )

    async def get_by_email(self, email: str) -> Optional[AdminModel]:
        async with self.app.database.session() as session:
            from sqlalchemy import select
            query = select(AdminModel).where(AdminModel.email == email)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_by_id(self, admin_id: int) -> Optional[AdminModel]:
        async with self.app.database.session() as session:
            return await session.get(AdminModel, admin_id)

    async def create_admin(self, email: str, password: str) -> AdminModel:
        async with self.app.database.session() as session:
            # Проверяем, существует ли уже такой админ
            existing = await self.get_by_email(email)
            if existing:
                return existing
            
            # Хешируем пароль
            password_hash = sha256(password.encode()).hexdigest()
            
            # Создаем админа
            admin = AdminModel(email=email, password=password_hash)
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            return admin