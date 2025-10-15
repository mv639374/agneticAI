# agenticAI/backend/app/db/postgres.py

"""
PostgreSQL Database Connection using SQLAlchemy 2.0 Async

This module handles:
1. Async database session management
2. Connection pooling for performance
3. Langgraph checkpointer integration for agent state persistence
4. Hot reload mechanism for caching frequently accessed data

Key Concepts:
- AsyncEngine: Async-compatible database engine
- AsyncSession: Async database session for queries
- sessionmaker: Factory for creating sessions
- Connection pooling: Reuses connections for better performance
"""

from contextlib import asynccontextmanager
from sys import exc_info
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.asyncio.session import async_session
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


# Base Model for Declarative ORM
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    All database models inherit from this class to get SQLAlchemy's ORM features.
    
    Example:
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String)
    """
    pass


# Database Engine Configuration
def create_database_engine() -> AsyncEngine:
    """
    Create async PostgreSQL engine with connection pooling.
    
    Connection Pool Settings:
    - pool_size: Number of connections to keep open (default: 5)
    - max_overflow: Additional connections beyond pool_size (default: 10)
    - pool_pre_ping: Check connection health before using (prevents stale connections)
    - pool_recycle: Recycle connections after N seconds (prevents timeout)
    - echo: Log all SQL statements (useful for debugging)
    
    Returns:
        AsyncEngine: Configured async database engine
    """
    # Development: Use NullPool for easier debugging (no connection reuse)
    # Production: Use QueuePool for better performance
    poolclass = NullPool if settings.DEBUG else QueuePool
    
    # NullPool doesn't accept pool_size, max_overflow, pool_pre_ping, or pool_recycle
    # These parameters only work with QueuePool
    if poolclass == NullPool:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,  # Log SQL in debug mode
            poolclass=poolclass,
        )
        log.info(
            "Database engine created",
            pool_class=poolclass.__name__,
            pool_size=0,
        )
    else:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,  # Log SQL in debug mode
            poolclass=poolclass,
            pool_size=5,  # Keep 5 connections open
            max_overflow=10,  # Allow up to 15 total connections (5+10)
            pool_pre_ping=True,  # Verify connections are alive
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        log.info(
            "Database engine created",
            pool_class=poolclass.__name__,
            pool_size=5,
        )
    
    return engine


# Create global engine instance
engine = create_database_engine()

# Create session factory
# expire_on_commit=False prevents SQLAlchemy from expiring objects after commit
# This is important for async code to avoid lazy-loading issues
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Database Initialization
async def init_database() -> None:
    """
    Initialize database by creating all tables.
    
    This should be called once at application startup.
    It creates tables for:
    - Conversations
    - Agent states
    - LangGraph checkpoints
    - User data
    """
    async with engine.begin() as conn:
        # Create all tables defined in Base subclasses
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables created/verified")


async def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        log.info("Database connection verified")
        return True
    except Exception as e:
        log.error("Database connection failed", exc_info=e)
        return False


async def close_database() -> None:
    """
    Close all database connections.
    This should be called at application shutdown.
    """
    await engine.dispose()
    log.info("Database connections closed")
