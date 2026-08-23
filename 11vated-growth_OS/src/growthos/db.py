"""Database engine and session management."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from growthos.config import get_settings


def build_engine(url: str | None = None) -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        url or settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


def build_session_factory(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine or build_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def close_engine(engine: AsyncEngine) -> None:
    await engine.dispose()


async def session_dependency(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a transactional session."""
    async with factory() as session:
        yield session
