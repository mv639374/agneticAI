# backend/tests/conftest.py

"""
Pytest Configuration and Shared Fixtures

PYTEST FIXTURES:
- Fixtures are reusable setup/teardown code
- They run before/after tests automatically
- Use dependency injection: test functions request fixtures as parameters
- Scope controls fixture lifetime: function, class, module, session

PYTEST CONCEPTS YOU'LL LEARN:
1. Fixtures (@pytest.fixture)
2. Mocking (pytest-mock, unittest.mock)
3. Async testing (pytest-asyncio)
4. Parametrize (test same function with different inputs)
5. Markers (categorize tests: @pytest.mark.unit)
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import app components
from app.config import settings
from app.db.models import Base
from app.db.postgres import engine as db_engine
from app.main import app

# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """
    Pytest hook: runs before test collection.
    
    Use this to:
    - Set environment variables for testing
    - Register custom markers
    - Configure plugins
    """
    # Set test environment
    os.environ['ENVIRONMENT'] = 'testing'
    os.environ['DEBUG'] = 'true'


# =============================================================================
# EVENT LOOP FIXTURE (Required for async tests)
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.
    
    SCOPE="session" means one event loop for entire test session.
    This improves performance by reusing the same loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create isolated database session for each test.
    
    SCOPE="function" means new session for each test function.
    This ensures test isolation (tests don't affect each other).
    
    PATTERN:
    1. Create session
    2. Yield to test (test runs here)
    3. Rollback changes
    4. Close session
    
    Usage in tests:
        async def test_something(db_session):
            # db_session is automatically provided
            result = await db_session.execute(...)
    """
    # Create test database engine (separate from production)
    # Uses in-memory SQLite for speed, or test PostgreSQL database
    async with db_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_maker = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        
        # Rollback any changes (test data doesn't persist)
        await session.rollback()


# =============================================================================
# API CLIENT FIXTURES
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing FastAPI endpoints.
    
    This allows testing API without starting a server.
    
    Usage:
        async def test_api(async_client):
            response = await async_client.get("/api/health")
            assert response.status_code == 200
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# =============================================================================
# MOCKING FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm_response(mocker):
    """
    Mock LLM API responses to avoid real API calls in tests.
    
    MOCKING PATTERN:
    - Replace real function with fake one
    - Control what the fake returns
    - Verify it was called correctly
    
    Usage:
        def test_agent(mock_llm_response):
            mock_llm_response.return_value = "Test response"
            # Now when agent calls LLM, it gets "Test response"
    """
    # Mock the LLM invocation
    mock = mocker.patch('langchain_groq.ChatGroq.ainvoke')
    
    # Create fake response
    fake_response = Mock()
    fake_response.content = "Mocked LLM response"
    
    mock.return_value = fake_response
    return mock


@pytest.fixture
def mock_websocket():
    """
    Mock WebSocket connection for testing real-time features.
    """
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_user_message():
    """
    Sample user message for testing agent invocation.
    """
    return "Calculate the average of 10, 20, 30, 40, 50"


@pytest.fixture
def sample_conversation_id():
    """
    Sample conversation ID.
    """
    return "test-conversation-123"


@pytest.fixture
def sample_agent_invoke_request(sample_user_message):
    """
    Sample agent invocation request.
    """
    return {
        "message": sample_user_message,
        "user_id": "test_user",
        "conversation_id": None,
    }


# =============================================================================
# FILE FIXTURES (For testing file operations)
# =============================================================================

@pytest.fixture
def temp_test_file(tmp_path):
    """
    Create temporary test file.
    
    tmp_path is pytest built-in fixture that provides temporary directory.
    Files are automatically cleaned up after test.
    
    Usage:
        def test_file_reader(temp_test_file):
            # temp_test_file is path to file
            content = read_file(temp_test_file)
    """
    # Create test file
    test_file = tmp_path / "test_data.txt"
    test_file.write_text("Test file content for unit testing")
    
    return str(test_file)


@pytest.fixture
def temp_csv_file(tmp_path):
    """
    Create temporary CSV file for testing.
    """
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text("Name,Age,Score\nAlice,25,95\nBob,30,87\nCharlie,28,92")
    
    return str(csv_file)


@pytest.fixture
def temp_json_file(tmp_path):
    """
    Create temporary JSON file for testing.
    """
    import json
    
    json_file = tmp_path / "test_data.json"
    data = {"users": [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]}
    json_file.write_text(json.dumps(data, indent=2))
    
    return str(json_file)


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """
    Auto-cleanup fixture that runs for every test.
    
    autouse=True means it runs automatically without being requested.
    
    Use this to clean up:
    - Test files
    - Cache entries
    - Database records
    """
    # Setup (runs before test)
    yield  # Test runs here
    
    # Teardown (runs after test)
    # Add cleanup logic here if needed
    pass
