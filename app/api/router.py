from fastapi import APIRouter

from app.api.routes import (
    app_releases,
    auth,
    billing,
    clients,
    devices,
    email_verification,
    health,
    password_reset,
    shades,
    showroom,
    usage,
)
from app.services import email_events  # noqa: F401  (registers the payment receipt email listener)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(password_reset.router)
api_router.include_router(email_verification.router)
api_router.include_router(usage.router)
api_router.include_router(clients.router)
api_router.include_router(shades.router)
api_router.include_router(showroom.router)
api_router.include_router(devices.router)
api_router.include_router(app_releases.router)
api_router.include_router(billing.router)
