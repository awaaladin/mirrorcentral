from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.admin.deps import AdminAuthRequired, AdminForbidden
from app.admin.router import admin_router
from app.api.router import api_router
from app.config import get_settings
from app.logging_config import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Starting Mirror backend (environment=%s, enhance_provider=%s)", settings.environment, settings.enhance_provider)
    yield
    logger.info("Shutting down Mirror backend")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Mirror Backend",
        description="Pro/business-tier backend for the Mirror makeup simulation app.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.admin_session_secret_effective,
        session_cookie="mirror_admin_session",
        same_site="lax",
        https_only=settings.environment == "production",
    )

    @app.exception_handler(AdminAuthRequired)
    async def _admin_auth_required(request: Request, exc: AdminAuthRequired) -> RedirectResponse:
        return RedirectResponse(url=f"/admin/login?next={exc.next_path}", status_code=303)

    @app.exception_handler(AdminForbidden)
    async def _admin_forbidden(request: Request, exc: AdminForbidden) -> RedirectResponse:
        return RedirectResponse(url="/admin/", status_code=303)

    app.include_router(api_router)
    app.include_router(admin_router)
    return app


app = create_app()
