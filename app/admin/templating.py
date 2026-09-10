from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.admin.deps import pop_flashes
from app.models.admin_user import AdminUser

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _format_datetime(value: datetime | None, fmt: str = "%d %b %Y, %H:%M") -> str:
    return value.strftime(fmt) if value else "—"


templates.env.filters["fmt_datetime"] = _format_datetime


def render(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    *,
    admin: AdminUser | None = None,
    active: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    """Render an admin template with the flash/nav/auth context every page needs."""
    ctx: dict[str, Any] = {
        "flashes": pop_flashes(request),
        "admin": admin,
        "active": active,
    }
    if context:
        ctx.update(context)
    return templates.TemplateResponse(request, template_name, ctx, status_code=status_code)
