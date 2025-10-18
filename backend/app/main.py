# agenticAI/backend/app/main.py

"""
FastAPI Application Entry Point

This is the main FastAPI application that:
1. Initializes logging
2. Configures middleware (CORS, request logging, error handling)
3. Mounts API routes
4. Provides health check endpoint

----------------------------------------------------------------------

Order of Execution:

The route mounting happens during the module import phase (which is why it logs first), but the actual route handling code doesn't execute until after the lifespan's startup completes. The order in the file doesn't determine execution order - Python first executes all module-level code (including route registrations), then runs the lifespan when the server starts.

This is why you see:

"All API routes mounted" (during import)
"Application starting" (when lifespan starts)
Database/Redis initialization
"Application startup complete" (after lifespan's yield)

The routes are registered early, but they can't be used until the lifespan's startup completes.


"""

# ============================================================================
# STEP 1: Suppress warnings FIRST - before ANY other imports
# ============================================================================
import warnings
import logging

# Suppress ALL warnings (most aggressive approach)
warnings.simplefilter("ignore")

# Or be more specific but catch custom warning classes too
warnings.filterwarnings("ignore")

# Disable SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').disabled = True
logging.getLogger('sqlalchemy.engine.Engine').disabled = True


# ============================================================================
# STEP 2: Now import everything else
# ============================================================================
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.logger import bind_context, clear_context, get_logger, setup_logging 
from psycopg.pq import error_message  
from app.api.routes import agents, conversations, health
from app.api.websockets import agent_updates

# Logging Setup (must be first)
# setup_logging()
log = get_logger(__name__)
STARTUP_TIME = None


# Lifespan Context Managers (It manages application's lifecycle and manages resources)
# Mitigates the older @app.on_event('startup') and @app.on_event('shutdown'), Because
# More structured and maintainable, Better error handling and built in async/await support.
# Cleaner Code: Groups related startup/shutdown logic together
# Testability: Makes it easier to test startup/shutdown behavior
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI application."""
    # Startup
    global STARTUP_TIME
    startup_start = time.time()
    
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
    
    # Calculate and display startup time
    STARTUP_TIME = time.time() - startup_start
    
    # Print startup time immediately after initialization completes
    print(f"\n{'='*80}")
    print(f"🚀 Application startup completed in {STARTUP_TIME:.2f} seconds")
    print(f"{'='*80}\n")
    
    
    yield  # Application runs here
    # yield Marks the boundary between startup and shutdown.
    
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


# =============================================================================
# MOUNT ROUTERS
# =============================================================================

# Health routes (no prefix, direct access)
app.include_router(health.router, prefix="/api")

# Agent routes
app.include_router(agents.router, prefix="/api")

# Conversation routes
app.include_router(conversations.router, prefix="/api")

# WebSocket routes
app.include_router(agent_updates.router)

log.info("All API routes mounted")



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
    2. Returns a consistent error response
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


# Allows you to run the application directly 
# The if __name__ == "__main__": part ensures this code only runs when 
# the file is executed directly, not when it's imported as a module.
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main.app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

# Uvicorn is a web server. It handles network communication - receiving 
# requests from client applications such as users' browsers and sending 
# responses to them. It communicates with FastAPI using the Asynchronous 
# Server Gateway Interface (ASGI), a standard API for Python web servers 
# that run asynchronous code.