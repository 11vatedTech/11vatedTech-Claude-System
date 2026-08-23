"""Integration test fixtures.

Integration tests use an ISOLATED test database (``TEST_DATABASE_URL``,
defaulting to ``growthos_test`` on the local PostgreSQL instance). Infrastructure
failures are hard failures: silently skipping them hides broken verification.
Test data never touches production storage.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import growthos.domain.models  # noqa: F401
from growthos.domain.base import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://growthos:growthos@127.0.0.1:5432/growthos_test",
)


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncEngine:
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.connect():
            pass
    except Exception as exc:  # noqa: BLE001
        await engine.dispose()
        pytest.fail(f"Integration database unavailable: {exc}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _truncate_all(engine: AsyncEngine):
    """Give every test a clean slate: truncate all tables after each test.

    Tests may commit (cross-transaction assertions need it); truncation
    restores isolation so committed rows cannot leak between tests.
    """
    yield
    async with engine.begin() as conn:
        tables = list(Base.metadata.sorted_tables)
        names = ", ".join(f'"{t.name}"' for t in tables)
        if names:
            await conn.execute(sa.text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncSession:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def session_factory(engine: AsyncEngine):
    return async_sessionmaker(engine, expire_on_commit=False)
