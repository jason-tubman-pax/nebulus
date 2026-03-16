"""Read-only share view by token (for public share link)."""
from fastapi import APIRouter, HTTPException

from app.services.config_store import config_store

router = APIRouter()


@router.get("/share/verify/{token}")
def verify_share_token(token: str) -> dict:
    """Verify token and return whether share view is allowed. Frontend uses this to show dashboard."""
    cfg = config_store.get()
    if not cfg.share_token or cfg.share_token != token:
        raise HTTPException(status_code=404, detail="Invalid or missing share token")
    return {"valid": True}
