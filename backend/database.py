import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

logger = logging.getLogger("sentinel.database")

# Environment DB URL or SQLite fallback for zero-friction local development
RAW_DB_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./sentinel_dev.db"
)

# Ensure SQLite parent directory exists before engine connects (Render ephemeral disk)
if RAW_DB_URL.startswith("sqlite"):
    _sqlite_path = RAW_DB_URL.split("///", 1)[-1]
    if _sqlite_path and _sqlite_path not in (":memory:", "/:memory:"):
        _dir = os.path.dirname(_sqlite_path)
        if _dir:
            os.makedirs(_dir, exist_ok=True)

# Handle postgresql:// to postgresql+asyncpg:// normalization
if RAW_DB_URL.startswith("postgresql://"):
    ASYNC_DB_URL = RAW_DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DB_URL = RAW_DB_URL

# Fallback to sync sqlite if aiosqlite is not installed
try:
    if ASYNC_DB_URL.startswith("sqlite"):
        import aiosqlite
    engine = create_async_engine(
        ASYNC_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False} if ASYNC_DB_URL.startswith("sqlite") else {}
    )
except ImportError:
    logger.warning("aiosqlite driver not found, falling back to memory/sync sqlite engine.")
    ASYNC_DB_URL = "sqlite:///./sentinel_dev.db"
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    sync_engine = create_engine(ASYNC_DB_URL, connect_args={"check_same_thread": False})
    # Async wrapper around sync engine for local dev fallback
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    """Dependency for providing database sessions per endpoint request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
