# backend/tests/test_api/test_websockets.py

"""
Tests for WebSocket Connections

Tests real-time agent update streaming.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = [pytest.mark.integration, pytest.mark.websocket]


class TestWebSocketConnections:
    """Tests for WebSocket functionality."""
    
    def test_websocket_connection(self):
        """
        Test basic WebSocket connection.
        
        Note: WebSocket testing in pytest requires synchronous client.
        For async WebSocket testing, consider using websockets library.
        """
        client = TestClient(app)
        
        # Connect to WebSocket
        with client.websocket_connect("/ws/agents/test-client-123") as websocket:
            # Receive welcome message
            data = websocket.receive_json()
            
            assert data["type"] == "connected"
            assert "client_id" in data
    
    def test_websocket_ping_pong(self):
        """Test WebSocket ping-pong keepalive."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/agents/test-ping-123") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({
                "type": "ping",
                "timestamp": "2025-01-01T00:00:00Z"
            })
            
            # Receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    def test_websocket_subscribe_to_conversation(self):
        """Test subscribing to specific conversation updates."""
        client = TestClient(app)
        
        with client.websocket_connect("/ws/agents/test-sub-123") as websocket:
            # Skip welcome
            websocket.receive_json()
            
            # Subscribe
            websocket.send_json({
                "type": "subscribe",
                "conversation_id": "test-conv-456"
            })
            
            # Receive subscription confirmation
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            assert response["conversation_id"] == "test-conv-456"
