# backend/tests/test_utils/test_logger.py

"""
Tests for Logging Utilities

Verifies structured logging works correctly.
"""

import pytest
from app.utils.logger import get_logger, bind_context, clear_context

pytestmark = pytest.mark.unit


class TestLogger:
    """Tests for logging functionality."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test")
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
    
    def test_bind_context_and_clear(self):
        """Test context binding and clearing."""
        # Bind context
        bind_context(request_id="test-123", user_id="user-456")
        
        # Clear context
        clear_context()
        
        # Should not raise errors
        assert True
    
    def test_logger_log_levels(self):
        """Test different log levels work."""
        logger = get_logger("test_levels")
        
        # Should not raise errors
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
