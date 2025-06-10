from datetime import datetime
import logging
from contextlib import asynccontextmanager
import os
import subprocess
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from config import settings
from models import Base, Car

logger = logging.getLogger(__name__)

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_LEVEL == "DEBUG",
)

# Create async session maker
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Drop existing tables if any
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_db() -> AsyncSession:
    """Provide a transactional scope around a series of operations."""
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        await session.close()


async def save_cars(cars: list[Car]):
    """Save cars to database with proper connection handling"""
    try:
        async with get_db() as session:
            session.add_all(cars)
            await session.commit()
    except Exception as e:
        logger.error(f"Error saving cars: {str(e)}")


async def car_exists(url: str) -> bool:
    """Check if car exists in database"""
    try:
        async with get_db() as session:
            result = await session.execute(select(Car).where(Car.url == url))
            return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.error(f"Error checking car existence {url}: {str(e)}")
        return False


async def dump_database():
    """Create a backup of the database using pg_dump."""
    try:
        backup_dir = "database_backups"
        os.makedirs(backup_dir, exist_ok=True)

        filename = f"{backup_dir}/backup_{datetime.now():%Y%m%d_%H%M}.sql"

        command = [
            "pg_dump",
            "-h",
            settings.DB_HOST,
            "-U",
            settings.POSTGRES_USER,
            "-d",
            settings.POSTGRES_DB,
            "-f",
            filename,
        ]

        subprocess.run(command, check=True)
        logger.info(f"Backup created successfully: {filename}")

    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
