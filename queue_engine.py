# queue_engine.py
# Arkadia — Oversoul Load-Balanced Queue Engine

import asyncio
import time
from typing import Callable, List, Dict, Any


class ArkadiaQueue:
    def __init__(self, min_interval: float = 3.5):
        self.queue: List[Dict[str, Any]] = []
        self.min_interval = min_interval
        self._last_call_time = 0.0
        self._running = False

    def add(self, sender: str, message: str, callback: Callable[[str, str], Any]):
        item = {
            "sender": sender,
            "message": message,
            "callback": callback,
            "timestamp": time.time(),
        }
        self.queue.append(item)

    async def _consume(self):
        if self._running:
            return

        self._running = True

        while self.queue:
            job = self.queue.pop(0)

            elapsed = time.time() - self._last_call_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)

            try:
                await job["callback"](job["sender"], job["message"])
            except Exception as e:
                print("[Queue] Error:", e)

            self._last_call_time = time.time()

        self._running = False

    async def process(self):
        await self._consume()

    def length(self) -> int:
        return len(self.queue)
