# queue_engine.py
# Arkadia — Oversoul Load-Balanced Queue Engine (Phase III)
# Ensures Arkana never rate-limits, overloads, or collapses under heavy traffic.

import asyncio
import time
from typing import Callable, List, Dict, Any

class ArkadiaQueue:
    def __init__(self, min_interval: float = 3.5):
        """
        min_interval = minimum delay (seconds) between Gemini calls.
        Adjust later depending on quota.
        """
        self.queue: List[Dict[str, Any]] = []
        self.min_interval = min_interval
        self._last_call_time = 0.0
        self._running = False

    def add(self, sender: str, message: str, callback: Callable):
        """
        Adds a request to the queue.
        callback = async function to execute once the queue reaches it.
        """
        item = {
            "sender": sender,
            "message": message,
            "callback": callback,
            "timestamp": time.time(),
        }
        self.queue.append(item)

    async def _consume(self):
        """Main loop that processes messages one-by-one."""
        if self._running:
            return  # Already running

        self._running = True

        while self.queue:
            job = self.queue.pop(0)

            # Enforce rate limit spacing
            elapsed = time.time() - self._last_call_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)

            # Execute callback
            try:
                await job["callback"](job["sender"], job["message"])
            except Exception as e:
                print("[Queue] Error processing job:", e)

            self._last_call_time = time.time()

        self._running = False

    async def process(self):
        """External trigger to start consumption."""
        await self._consume()

    def length(self):
        return len(self.queue)
