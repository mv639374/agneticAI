# agenticAI/backend/app/api/websockets/agent_updates.py

"""
WebSocket for Real-time Agent Updates

Provides live streaming of agent execution progress.
"""

import asyncio
import json
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter()


# =============================================================================
# CONNECTION MANAGER
# =============================================================================
class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Supports:
    - Multiple concurrent connections
    - Broadcast to all connections
    - Send to specific connection
    - Automatic cleanup on disconnect
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Accept new WebSocket connection.
        
        Args:
            websocket: WebSocket instance
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        log.info("WebSocket connected", client_id=client_id, total_connections=len(self.active_connections))
    
    def disconnect(self, client_id: str):
        """
        Remove disconnected client.
        
        Args:
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            log.info("WebSocket disconnected", client_id=client_id, total_connections=len(self.active_connections))
    
    async def send_personal_message(self, message: dict, client_id: str):
        """
        Send message to specific client.
        
        Args:
            message: Message payload
            client_id: Target client identifier
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                log.error("Failed to send message", client_id=client_id, exc_info=e)
    
    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message payload
        """
        disconnected = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                log.error("Broadcast failed", client_id=client_id, exc_info=e)
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)


# Global connection manager instance
manager = ConnectionManager()


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================
@router.websocket("/ws/agents/{client_id}")
async def agent_updates_websocket(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time agent updates.
    
    Protocol:
    1. Client connects with unique client_id
    2. Server accepts connection
    3. Server sends updates as agents execute
    4. Client can send messages to trigger actions
    
    Message Format (Server -> Client):
    {
        "type": "agent_started" | "agent_progress" | "agent_completed" | "error",
        "agent_name": "analysis_agent",
        "data": {...},
        "timestamp": "2025-10-16T00:00:00Z"
    }
    
    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
    """
    await manager.connect(websocket, client_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connected",
                "message": "Connected to agent update stream",
                "client_id": client_id,
            },
            client_id,
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                
                # Parse message
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await manager.send_personal_message(
                        {
                            "type": "error",
                            "message": "Invalid JSON format",
                        },
                        client_id,
                    )
                    continue
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    await manager.send_personal_message(
                        {
                            "type": "pong",
                            "timestamp": message.get("timestamp"),
                        },
                        client_id,
                    )
                
                elif message_type == "subscribe":
                    # Subscribe to specific conversation updates
                    conversation_id = message.get("conversation_id")
                    await manager.send_personal_message(
                        {
                            "type": "subscribed",
                            "conversation_id": conversation_id,
                        },
                        client_id,
                    )
                
                else:
                    log.warning("Unknown message type", message_type=message_type, client_id=client_id)
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                log.error("WebSocket error", client_id=client_id, exc_info=e)
                break
    
    finally:
        manager.disconnect(client_id)


# =============================================================================
# HELPER FUNCTIONS FOR SENDING UPDATES
# =============================================================================
async def send_agent_update(
    client_id: str,
    update_type: str,
    agent_name: str,
    data: dict,
):
    """
    Send agent update to specific client.
    
    Args:
        client_id: Target client identifier
        update_type: Type of update (started, progress, completed, error)
        agent_name: Name of agent
        data: Update payload
    """
    from datetime import datetime
    
    message = {
        "type": update_type,
        "agent_name": agent_name,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    await manager.send_personal_message(message, client_id)


async def broadcast_agent_update(
    update_type: str,
    agent_name: str,
    data: dict,
):
    """
    Broadcast agent update to all connected clients.
    
    Args:
        update_type: Type of update
        agent_name: Name of agent
        data: Update payload
    """
    from datetime import datetime
    
    message = {
        "type": update_type,
        "agent_name": agent_name,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    await manager.broadcast(message)