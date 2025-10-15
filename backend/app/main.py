# agenticAI/backend/app/main.py

"""
FastAPI Application Entry Point

This is the main FastAPI application that:
1. Initializes logging
2. Configures middleware (CORS, request logging, error handling)
3. Mounts API routes
4. Provides health check endpoint
"""


import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.logger import bind_context, clear_context, get_logger, setup_logging
from psycopg.pq import error_message


# Logging Setup (must be first)
setup_logging()
log = get_logger(__name__)

# Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI application."""
    # Startup
    log.info("Application starting", environment=settings.ENVIRONMENT, debug=settings.DEBUG)
    
    # Initialize databases
    from app.db.postgres import init_database, check_database_connection
    from app.db.redis_cache import init_cache
    from app.db.vector_store import init_vector_store
    
    # Check PostgreSQL connection
    if await check_database_connection():
        await init_database()
    else:
        log.error("Failed to connect to PostgreSQL")
    
    # Initialize Redis cache
    await init_cache()
    
    # Initialize vector store
    await init_vector_store()
    
    log.info("All database connections initialized")
    
    yield  # Application runs here
    
    # Shutdown
    log.info("Application shutting down")
    
    from app.db.postgres import close_database
    from app.db.redis_cache import close_cache
    from app.db.vector_store import close_vector_store
    
    await close_database()
    await close_cache()
    await close_vector_store()


# FastAPI App Initialization
app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous Multi-Agent Enterprise Intelligence System",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Request logging middleware.
    
    This middleware:
    1. Generates unique request ID
    2. Binds request context (method, path, client IP)
    3. Logs request start and completion
    4. Measures request duration
    5. Clears context after request
    """
    # Clear any existing context (prevents leakage between requests)
    clear_context()

    # Generate unique request ID
    request_id = str(uuid.uuid4())

    # Bind context for this request
    bind_context(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
    )

    # Log request start
    log.info("Request started")

    try:
        # Process request
        response = await call_next(request)

        # Log request completion
        log.info(
            "Request completed",
            status_code=response.status_code,
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as exc:
        log.error(
            "Request failed",
            exc_info=exc,
            error=str(exc),
        )
        raise
    finally:
        # Clear context after request
        clear_context()


# Health Check Endpoint
@app.get(
    "/api/health",
    tags=["Health"],
    summary="Health check endpoint",
    response_description="Service health status",
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Service status and metadata
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
    }


@app.get(
    "/",
    tags=["Root"],
    summary="Root endpoint",
)
async def root():
    """
    Root endpoint.

    Returns:
        dict: Welcome messsage
    """
    return {
        "message": "Autonomous Multi-Agent Enterprise Intelligence System",
        "docs": "/docs",
        "health": "/api/health",
    }


# Error Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.

    This catches all exceptions that aren't handled elsewhere and:
    1. Logs the error with full context
    2. Returns aa consistent error response
    3. Prevents sensitive information leakage
    """
    log.error(
        "Unhandled exception",
        exc_info=exc,
        error_type=type(exc).__name__,
        error_message=str(exc),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occured",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main.app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )







@app.get("/")
def root():
    return {"status":"chal rha hai bhai!"}

@app.get("/api/health")
def health_check():
    return {"status":"OK"}