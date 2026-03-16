"""Pax Nebulus - FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.services.modbus_service import modbus_service
from app.api import live, system, tunnel, wifi, share, storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import init_db
    await init_db()
    modbus_service.start()
    yield
    modbus_service.stop()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(live.router, prefix="/api", tags=["live"])
app.include_router(system.router, prefix="/api", tags=["system"])
app.include_router(tunnel.router, prefix="/api", tags=["tunnel"])
app.include_router(wifi.router, prefix="/api", tags=["wifi"])
app.include_router(share.router, prefix="/api", tags=["share"])
app.include_router(storage.router, prefix="/api", tags=["storage"])


@app.get("/health")
def health():
    return {"status": "ok"}


# Mount frontend static build when present (e.g. in production)
_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
