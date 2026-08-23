"""Single-founder authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select

from growthos.api.csrf import CSRF_COOKIE
from growthos.api.deps import FounderDep, SessionDep, new_csrf_token
from growthos.config import get_settings
from growthos.domain.models_system import Founder, Session
from growthos.security import passwords, sessions
from growthos.security.sessions import cleanup_sessions, revoke_session

router = APIRouter(prefix="/auth", tags=["auth"])


class BootstrapIn(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12)
    phone: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12)


def _set_session_cookie(response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=settings.session_ttl_seconds,
        path="/",
    )


def _set_csrf_cookie(response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=CSRF_COOKIE,
        value=token,
        httponly=False,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )


@router.get("/csrf")
async def csrf(request: Request):
    token = new_csrf_token()
    response: object = JSONResponse({"csrf_token": token})
    _set_csrf_cookie(response, token)
    return response


@router.post("/bootstrap", status_code=201)
async def bootstrap(session: SessionDep, body: BootstrapIn):
    """Create the single founder account on first boot (no account may exist)."""
    existing = await session.scalar(select(func.count(Founder.id)))
    if existing:
        raise HTTPException(status_code=409, detail="Founder already exists")

    if get_settings().require_strong_password and not passwords.is_strong_password(
        body.password
    ):
        raise HTTPException(
            status_code=422,
            detail="Password must be 12+ chars with upper, lower, and a digit",
        )

    founder = Founder(
        email=body.email,
        display_name=body.display_name,
        password_hash=passwords.hash_password(body.password),
        phone=body.phone,
    )
    session.add(founder)
    await session.flush()

    token, _ = await sessions.create_session(session, founder.id)
    await cleanup_sessions(session)  # best-effort hygiene on first boot
    response = JSONResponse(
        status_code=201,
        content={
            "id": founder.id,
            "email": founder.email,
            "display_name": founder.display_name,
        },
    )
    _set_session_cookie(response, token)
    _set_csrf_cookie(response, new_csrf_token())
    return response


@router.post("/login")
async def login(session: SessionDep, body: LoginIn):
    result = await session.execute(
        select(Founder).where(Founder.email == body.email)
    )
    founder = result.scalar_one_or_none()
    if founder is None or not passwords.verify_password(
        founder.password_hash, body.password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not founder.is_active:
        raise HTTPException(status_code=401, detail="Account disabled")

    token, _ = await sessions.create_session(session, founder.id)
    await cleanup_sessions(session)  # best-effort hygiene on login
    response = JSONResponse(
        content={
            "id": founder.id,
            "email": founder.email,
            "display_name": founder.display_name,
        }
    )
    _set_session_cookie(response, token)
    _set_csrf_cookie(response, new_csrf_token())
    return response


@router.post("/logout")
async def logout(request: Request, session: SessionDep, founder: FounderDep):
    record = request.state.session_record
    result = await session.execute(select(Session).where(Session.id == record.id))
    sess = result.scalar_one_or_none()
    if sess:
        await revoke_session(session, sess, reason="founder logout", actor=founder.email)
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(get_settings().session_cookie_name)
    return response


@router.get("/me")
async def me(founder: FounderDep):
    return {
        "id": founder.id,
        "email": founder.email,
        "display_name": founder.display_name,
        "phone": founder.phone,
    }


@router.post("/change-password")
async def change_password(
    session: SessionDep, founder: FounderDep, body: ChangePasswordIn
):
    if not passwords.verify_password(founder.password_hash, body.current_password):
        raise HTTPException(status_code=401, detail="Current password incorrect")
    if get_settings().require_strong_password and not passwords.is_strong_password(
        body.new_password
    ):
        raise HTTPException(
            status_code=422,
            detail="New password must be 12+ chars with upper, lower, and a digit",
        )
    founder.password_hash = passwords.hash_password(body.new_password)
    return {"ok": True}
