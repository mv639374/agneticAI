# backend/tests/test_config/test_settings.py

"""
Tests for Configuration Management

Verifies settings load correctly from environment.
"""

import pytest
import os
from app.config import settings

pytestmark = pytest.mark.unit


class TestConfiguration:
    """Tests for application configuration."""
    
    def test_settings_loaded(self):
        """Test that settings are loaded correctly."""
        assert settings is not None
        assert settings.APP_NAME is not None
        assert settings.ENVIRONMENT is not None
    
    def test_environment_is_testing(self):
        """Test that test environment is set."""
        # This is set in conftest.py pytest_configure
        assert settings.ENVIRONMENT in ["testing", "development"]
    
    def test_database_url_format(self):
        """Test database URL is properly formatted."""
        db_url = settings.DATABASE_URL
        assert db_url.startswith("postgresql")
        assert "asyncpg" in db_url or "psycopg" in db_url
    
    def test_llm_provider_configured(self):
        """Test LLM provider is configured."""
        assert settings.DEFAULT_LLM_PROVIDER in ["groq", "google"]
    
    def test_api_keys_not_empty(self):
        """Test that required API keys are set."""
        # Note: In testing, these might be dummy values
        assert len(settings.GROQ_API_KEY) > 0
        assert len(settings.GOOGLE_API_KEY) > 0
