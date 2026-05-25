"""WebSocket connection manager (used for future multi-client broadcast)."""

from __future__ import annotations
import asyncio
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(session_id, []).append(ws)

    def disconnect(self, session_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(session_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, session_id: str, data: dict) -> None:
        for ws in list(self._connections.get(session_id, [])):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(session_id, ws)


manager = ConnectionManager()
