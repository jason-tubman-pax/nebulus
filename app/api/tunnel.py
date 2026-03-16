"""Public share link (tunnel) management."""
from fastapi import APIRouter

from app.models.settings import TunnelState
from app.services.tunnel_service import tunnel_service, generate_share_token
from app.services.config_store import config_store

router = APIRouter()


@router.get("/tunnel", response_model=TunnelState)
def get_tunnel_state() -> TunnelState:
    return TunnelState(
        enabled=tunnel_service.is_running,
        share_url=tunnel_service.share_url,
        tunnel_type="cloudflare",
        error=tunnel_service.error,
    )


@router.post("/tunnel/start")
def start_tunnel() -> TunnelState:
    tunnel_service.start()
    return get_tunnel_state()


@router.post("/tunnel/stop")
def stop_tunnel() -> TunnelState:
    tunnel_service.stop()
    return get_tunnel_state()


@router.post("/tunnel/share-token")
def regenerate_share_token() -> dict:
    """Generate a new random token for /share/{token} read-only view."""
    cfg = config_store.get()
    cfg.share_token = generate_share_token()
    config_store.set(cfg)
    return {"share_token": cfg.share_token}
