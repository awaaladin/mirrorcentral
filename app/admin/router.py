from fastapi import APIRouter

from app.admin.routes import (
    admins,
    audit,
    auth,
    clients,
    dashboard,
    enhance_jobs,
    shades,
    subscriptions,
    users,
)

admin_router = APIRouter()
for _module in (auth, dashboard, users, subscriptions, enhance_jobs, shades, clients, audit, admins):
    admin_router.include_router(_module.router)
