# agenticAI/backend/app/api/middleware/auth.py

"""
Authentication Middleware

Provides API key authentication for protected endpoints.
"""

from fastapi import Header, HTTPException, status

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


async def verify_api_key(x_api_key: str = Header(..., description="API Key")):
    """
    Verify API key from request header.
    
    Usage in routes:
        @router.get("/protected", dependencies=[Depends(verify_api_key)])
        async def protected_endpoint():
            return {"message": "Authenticated"}
    
    Args:
        x_api_key: API key from X-API-Key header
    
    Raises:
        HTTPException: If API key is invalid
    """
    if x_api_key != settings.API_KEY:
        log.warning("Invalid API key attempt", provided_key=x_api_key[:10] + "...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return x_api_key