from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.adapters.driven.persistence.database.models.user import UserModel
from app.core.domain.entities.user import User
from app.core.domain.value_objects import UserId, UserRole
from app.core.ports.driven.user_repository import UserRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PgUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UserId) -> User:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            raise ValueError(f"User {user_id} not found")
        return self._model_to_entity(model)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_itmo_id(self, itmo_id: str) -> User | None:
        stmt = select(UserModel).where(UserModel.itmo_id == itmo_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def create(self, user: User) -> User:
        model = self._entity_to_model(user)
        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)

    async def update(self, user: User) -> User:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"User {user.id} not found")
        model.email = user.email
        model.name = user.name
        model.role = user.role.value
        model.password_hash = user.password_hash
        model.itmo_id = user.itmo_id
        model.itmo_refresh_token = user.itmo_refresh_token
        model.created_at = user.created_at
        await self._session.flush()
        return self._model_to_entity(model)

    @staticmethod
    def _entity_to_model(entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=entity.email,
            name=entity.name,
            role=entity.role.value,
            password_hash=entity.password_hash,
            itmo_id=entity.itmo_id,
            itmo_refresh_token=entity.itmo_refresh_token,
            created_at=entity.created_at,
        )

    @staticmethod
    def _model_to_entity(model: UserModel) -> User:
        return User(
            id=UserId(model.id),
            email=model.email,
            name=model.name,
            role=UserRole(model.role),
            itmo_id=model.itmo_id,
            created_at=model.created_at,
            password_hash=model.password_hash,
            itmo_refresh_token=model.itmo_refresh_token,
        )
