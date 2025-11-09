import asyncio
from typing import Dict, Set

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        # tenant_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        async with self.lock:
            if tenant_id not in self.active_connections:
                self.active_connections[tenant_id] = set()
            self.active_connections[tenant_id].add(websocket)
        print(f"✓ WebSocket connected for tenant: {tenant_id}")

    async def disconnect(self, websocket: WebSocket, tenant_id: str):
        async with self.lock:
            if tenant_id in self.active_connections:
                self.active_connections[tenant_id].discard(websocket)
                if not self.active_connections[tenant_id]:
                    del self.active_connections[tenant_id]
        print(f"✓ WebSocket disconnected for tenant: {tenant_id}")

    async def broadcast(self, tenant_id: str, message: dict):
        """Broadcast message to all connections for a tenant"""
        async with self.lock:
            if tenant_id in self.active_connections:
                dead_connections = set()
                for connection in self.active_connections[tenant_id]:
                    try:
                        await connection.send_json(message)
                    except:
                        dead_connections.add(connection)

                # Remove dead connections
                for conn in dead_connections:
                    self.active_connections[tenant_id].discard(conn)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except:
            pass


manager = WebSocketManager()
