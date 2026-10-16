from fastapi import APIRouter

from app.api.routes import app_releases, auth, clients, devices, health, shades, showroom

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(clients.router)
api_router.include_router(shades.router)
api_router.include_router(showroom.router)
api_router.include_router(devices.router)
api_router.include_router(app_releases.router)
