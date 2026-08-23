"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from growthos.api.csrf import CSRFMiddleware
from growthos.api.routes import (
    agent,
    auth,
    campaigns,
    communications,
    evidence,
    health,
    inbox,
    integrations,
    jobs,
    opportunities,
    products,
    revenue,
    scout,
)
from growthos.config import get_settings
from growthos.db import build_engine, build_session_factory
from growthos.shared.errors import (
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    StateTransitionError,
    ValidationError,
)


def create_app(engine=None) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine or build_engine()
        app.state.session_factory = build_session_factory(app.state.engine)
        yield
        from growthos.db import close_engine

        await close_engine(app.state.engine)

    app = FastAPI(
        title="11vatedTech GrowthOS API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CSRFMiddleware)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(StateTransitionError)
    async def transition_handler(request: Request, exc: StateTransitionError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(PermissionDeniedError)
    async def permission_handler(request: Request, exc: PermissionDeniedError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def domain_handler(request: Request, exc: DomainError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    for router in (
        health.router,
        auth.router,
        agent.router,
        products.router,
        campaigns.router,
        opportunities.router,
        revenue.router,
        inbox.router,
        evidence.router,
        jobs.router,
        integrations.router,
        integrations.approvals_router,
        communications.router,
        scout.router,
    ):
        app.include_router(router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "service": "11vatedTech GrowthOS API",
            "status": "running",
            "docs": "/docs",
        }

    return app


app = create_app()
