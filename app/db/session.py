"""Async SQLite engine and session for dashboard history."""
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import Base

DB_PATH = settings.data_dir / "history.db"
# SQLAlchemy async SQLite URL
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Create tables if they don't exist. Call at app startup."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
