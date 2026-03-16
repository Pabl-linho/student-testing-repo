import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Default value is kept for local development, but the app can now be configured
# from the environment for staging/production handoff.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update(
        {
            "pool_size": 5,
            "max_overflow": 10,
        }
    )

# Create an asynchronous engine with connection pooling for better performance under load.
engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Factory for asynchronous sessions.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Declarative base class for ORM models.
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
