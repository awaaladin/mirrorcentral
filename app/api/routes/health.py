from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness check for the deploy platform. Deliberately has no DB/Redis dependency
    so it stays fast and reports up even if a downstream dependency is degraded."""
    return {"status": "ok"}
