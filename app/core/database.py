from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# TODO: Replace the following credentials with your PostgreSQL configuration.
DATABASE_URL = " "

# Create an asynchronous engine with connection pooling for better performance under load.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,       # Number of connections to keep open
    max_overflow=10    # Extra connections allowed during traffic spikes
)

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