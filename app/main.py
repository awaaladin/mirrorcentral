from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
    app = FastAPI(
        title="Mirror Backend",
        description="Pro/business-tier backend for the Mirror makeup simulation app.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()
