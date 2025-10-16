# agenticAI/backend/app/api/routes/health.py

"""
Health Check Endpoints

Provides health status for monitoring, load balancers, and uptime checks.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.config import settings
from app.db.postgres import check_database_connection
from app.db.redis_cache import cache
from app.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    environment: str
    version: str
    database: str
    cache: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check service health and component status",
)
async def health_check():
    """
    Comprehensive health check.
    
    Returns:
        Health status with component checks
    """
    # Check database
    db_status = "healthy" if await check_database_connection() else "unhealthy"
    
    # Check cache
    cache_status = "healthy" if cache.redis_client else "unavailable"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        environment=settings.ENVIRONMENT,
        version="0.1.0",
        database=db_status,
        cache=cache_status,
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Simple liveness check for Kubernetes",
)
async def liveness():
    """
    Kubernetes liveness probe.
    
    Returns 200 if service is running.
    """
    return {"status": "alive"}


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Check if service is ready to accept traffic",
)
async def readiness():
    """
    Kubernetes readiness probe.
    
    Returns 200 if service is ready to handle requests.
    """
    db_healthy = await check_database_connection()
    
    if not db_healthy:
        return {"status": "not ready", "reason": "database unavailable"}
    
    return {"status": "ready"}