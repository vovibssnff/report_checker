from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

engine: AsyncEngine = create_async_engine(settings.DATABASE_URL, echo=False)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Request-scoped session: commits on success, rollback on exception."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
