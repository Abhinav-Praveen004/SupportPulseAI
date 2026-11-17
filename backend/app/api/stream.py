"""Server-Sent Events (SSE) live streaming for real-time ticket, alert, and risk updates."""

import asyncio
from datetime import datetime, timezone
import json
from typing import Any, AsyncGenerator, Dict, Set
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from backend.app.core.logging import logger

router = APIRouter(tags=["stream"])


class StreamManager:
    """Manages active SSE client connections and event broadcasting."""

    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> asyncio.Queue:
        """Register a new client connection queue."""
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(queue)
        logger.info(f"SSE client connected. Active subscribers: {len(self.subscribers)}")
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        """Remove a disconnected client queue."""
        self.subscribers.discard(queue)
        logger.info(f"SSE client disconnected. Active subscribers: {len(self.subscribers)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event payload to all active subscribers."""
        if not self.subscribers:
            return

        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Deliver to all subscriber queues concurrently
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(payload)
            except Exception:
                pass


stream_manager = StreamManager()


@router.get("/stream")
async def event_stream(request: Request):
    """Server-Sent Events endpoint for real-time reactive updates."""
    queue = await stream_manager.subscribe()

    async def event_generator() -> AsyncGenerator[Dict[str, str], None]:
        try:
            # Send initial connected greeting
            yield {
                "event": "connected",
                "data": json.dumps({"status": "connected", "timestamp": datetime.now(timezone.utc).isoformat()}),
            }

            while True:
                # Check for client disconnect
                if await request.is_disconnected():
                    break

                try:
                    # Wait for message with 15s timeout for keepalive ping
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": payload["event"],
                        "data": json.dumps(payload["data"]),
                    }
                except asyncio.TimeoutError:
                    # Keepalive ping
                    yield {
                        "event": "ping",
                        "data": json.dumps({"time": datetime.now(timezone.utc).isoformat()}),
                    }
        finally:
            await stream_manager.unsubscribe(queue)

    return EventSourceResponse(event_generator())
