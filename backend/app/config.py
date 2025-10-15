# agentiAI/backend/app/config.py

"""
Configuration Management using Pydantic Settings v2

This module centralizes all application settings using pydantic's BaseSettings,
which provides automatic environment varaible loading, type declaration,
and structured configuration management.

Key Features:
- Automatic .env file loading
- Type validation for all settings
- Support for multiple LLM providers (Groq, Gemini)
- Database connection management (PostgreSQL, Redis, Vector DB)
- Security Settings (API keys, JWT secrets)
"""

import os
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import desc
from sqlalchemy.util import LRUCache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Pydantic automatically:
    1. Reads from .env file
    2. Converts environment variables to corect types
    3. Validates required fields
    4. Provides default values where specified
    """


    #-------------------------- Application Settings ----------------------------

    APP_NAME: str = Field(
        "Autonomous Multi-Agent System", 
        description="Application name for logging and monitoring"
    )
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Current environment"
    )
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode (verbose logging, auto-reload)"
    )
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: str = Field(default=8000, description="API server port")


    #--------------------------- LLM Provider Settings ---------------------------

    GROQ_API_KEY: str = Field(
        ...,
        description="Groq API key for LLM inference"
    )
    GOOGLE_API_KEY: str = Field(
        ...,
        description="Google AI Studio API key for Gemini models"
    )

    DEFAULT_LLM_PROVIDER: Literal['groq', 'google'] = Field(
        default="groq",
        description="Default LLM provider to use"
    )
    GROQ_MODEL_NAME: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model for agent reasoning"
    )
    GOOGLE_MODEL_NAME: str = Field(
        default="gemini-2.0-flash-exp",
        description="Google model for complex tasks"
    )


    #---------------------- Database Settings -----------------------------
    # Cloud PostgreSQL for:
    # - Conversation history storage
    # - LangGraph checkpointing (agent state persistence)
    # - User management

    POSTGRES_HOST: str = Field(..., description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(..., description="Database name")
    POSTGRES_USER: str = Field(..., description="Database user")
    POSTGRES_PASSWORD: str = Field(..., description="Database password")
    POSTGRES_SSL_MODE: str = Field(default="require", description="SSL mode")

    # Computed database URL for SQLAlchemy
    @property
    def DATABASE_URL(self) -> str:
        """
        Constructs async PostgreSQL connection string.
        Uses asyncpg driver for async operations with SQLAlchemy.
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            f"?ssl={self.POSTGRES_SSL_MODE}"
        )

    
    #-------------------- REDIS SETTINGS (Cloud Redis for caching) ----------------------
    # Used for:
    # - Agent execution state caching
    # - Session Management
    # - Rate limiting
    # - Hot reload mechanism (cache frequently accessed DB data)

    REDIS_HOST: str = Field(..., description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(..., description="Redis password")
    REDIS_DB: str = Field(..., description="Redis database")
    REDIS_SSL: bool = Field(default=False, description="Use SSL for Redis")

    @property
    def REDIS_URL(self) -> str:
        """
        Constructs Redis connection string.
        Supports both redis:// and rediss:// (SSL) protocols.
        """
        protocol = 'rediss' if self.REDIS_SSL else 'redis'
        auth = f"default:{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{protocol}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    ENABLE_CACHE: bool = Field(default=True, description="Enable Redis caching")
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds (1 hour)")
    CACHE_HOT_RELOAD_INTERVAL: int = Field(
        default=300,
        description="Interval to reload cache from PostgreSQL (5 minutes)"
    )


    #---------------------------- Vector Database Settings -----------------------------
    # Vector DB is used for:
    # - Semantic search in agent memory
    # - Document embeddings
    # - Conversation context retrieval

    VECTOR_DB_TYPE: Literal["pinecone", "chromadb"] = Field(
        default="pinecone",
        description="Vector database type"
    )

    # Pinecone settings
    PINECONE_API_KEY: Optional[str] = Field(default=None)
    PINECONE_ENVIRONEMENT: Optional[str] = Field(default="us-east-1")
    PINECONE_INDEX_NAME: Optional[str] = Field(default="agent-memory")

    # ChromaDB settings
    CHROMA_HOST: Optional[str] = Field(default="localhost")
    CHROMA_PORT: Optional[str] = Field(default=8000)
    CHROMA_COLLECTION_NAME: Optional[str] = Field(default="agent_embeddings")


    #------------------------ Security Settings ---------------------------------------

    API_KEY: str = Field(
        ...,
        min_length=32,
        description="API key for authentication"
    )
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="JWT secret key"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT token expiration time"
    )
    # CORS settings
    CORS_ORIGINS: str = Field(
        default="http://locallhost:3000,http://127.0.0.01:3000",
        description="Comma-seperated list of allowed CORS origins"
    )

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        """Convert comman-seperated CORS origins to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    
    #--------------------------------- Agent Configuration ---------------------------
    # These settings control agent behaviour and LLM interaction

    MAX_AGENT_INTEGRATIONS: int = Field(
        default=10,
        description="Maximum iterations for agent reasoning loop"
    )
    AGENT_TIMEOUT_SECONDS: int = Field(
        default=120,
        description="Timeout for agent execution (2 minutes)"
    )
    ENABLE_AGENT_MEMORY: bool = Field(
        default=True,
        description="Enable long-term memory for agents"
    )
    SUPERVISOR_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="LLM model for supervisor agent"
    )


    #------------------------- Logging Settings ---------------------------------------

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FORMAT: Literal["json", "console"] = Field(
        default="json",
        description="Log output format (json for production, console for dev)"
    )
    ENABLE_STRUCTURED_LOGGING: bool = Field(
        default=True,
        description="Enable structlog for structured logging"
    )


    #---------------------------- Pydantic Settings Configuration ----------------------

    model_config = SettingsConfigDict(
        env_file=".env",  # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=True,  # Environment variables are case-sensitive
        extra="ignore",  # Ignore extra environment variables
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache settings instance.

    Using @lru_cache ensures settings are loaded only once and reused
    across the application, imporoving the performance.

    Returns:
        Settings: Cached settings instance
    """
    return Settings()


# Expoert singleton instance
settings = get_settings()