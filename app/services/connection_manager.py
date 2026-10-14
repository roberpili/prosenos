import asyncio
import logging
from typing import Literal, TypedDict

from fastapi import WebSocket

from app.domain.enums import Sport

logger = logging.getLogger(__name__)


class LiveUpdateMessage(TypedDict):
    type: Literal["live_update"]
    sport: Sport
    matches: list[dict[str, object]]


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []
        self.last_state: LiveUpdateMessage | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)
        if self.last_state is not None and not await self._send(
            websocket, self.last_state
        ):
            self.disconnect(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def _send(self, ws: WebSocket, message: LiveUpdateMessage) -> bool:
        try:
            await asyncio.wait_for(ws.send_json(message), timeout=5)
            return True
        except Exception:
            logger.debug("dropping websocket", exc_info=True)
            return False

    async def broadcast(self, message: LiveUpdateMessage):
        self.last_state = message
        snapshot = list(self.active)
        results = await asyncio.gather(*(self._send(ws, message) for ws in snapshot))
        for ws, ok in zip(snapshot, results):
            if not ok:
                self.disconnect(ws)


manager = ConnectionManager()
