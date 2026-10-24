"""SQLAlchemy async engine and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )


engine = None
async_session_factory = None


def init_engine():
    global engine, async_session_factory
    engine = get_engine()
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Dependency that provides an async database session."""
    if async_session_factory is None:
        init_engine()
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
