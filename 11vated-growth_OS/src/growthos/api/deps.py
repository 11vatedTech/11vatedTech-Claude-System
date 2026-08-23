"""FastAPI dependencies."""

from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from growthos.config import get_settings
from growthos.domain.models_system import Founder
from growthos.security.sessions import resolve_session


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_factory


async def get_db(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_founder(
    request: Request, session: SessionDep
) -> Founder:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    session_record = await resolve_session(session, token)
    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalid or expired",
        )

    result = await session.execute(
        select(Founder).where(Founder.id == session_record.founder_id)
    )
    founder = result.scalar_one_or_none()
    if founder is None or not founder.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Founder account unavailable",
        )
    request.state.founder = founder
    request.state.session_record = session_record
    return founder


FounderDep = Annotated[Founder, Depends(get_current_founder)]


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)
