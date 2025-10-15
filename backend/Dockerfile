# =============================================================================
# STAGE 1: Builder - Install dependencies with uv
# =============================================================================
FROM python:3.12.3-slim-bookworm AS builder

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set uv environment variables for optimal Docker builds
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml ./

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock* ./

# Install dependencies (excluding dev dependencies)
# Using cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --no-dev --locked; \
    else \
        uv sync --no-dev; \
    fi



# Install dependencies (excluding dev dependencies)
# Using cache mount for faster rebuilds
# RUN --mount=type=cache,target=/root/.cache/uv \
#     uv sync --no-dev --locked

# Copy application source code
COPY app ./app
COPY data ./data

# =============================================================================
# STAGE 2: Runtime - Minimal production image
# =============================================================================
FROM python:3.12.3-slim-bookworm AS runtime

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client library
    libpq5 \
    curl \
    # Cleanup to reduce image size
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -u 1001 appuser

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser data ./data

# Set Python path to use virtual environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000



# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

# Start FastAPI with uvicorn
# Using 1 worker for Phase 1 (will scale with Celery in Phase 2)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
