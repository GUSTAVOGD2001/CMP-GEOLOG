"""Endpoint de salud para orquestación y monitoreo."""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Retorna estado operativo con timestamp UTC ISO 8601."""
    return {
        "status": "ok",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
