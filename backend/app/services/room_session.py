import asyncio
import threading
import queue
import logging
import time
from typing import Any, Callable, Optional
from concurrent.futures import Future

logger = logging.getLogger(__name__)


class RoomSession:
    def __init__(self, room_id: str, idle_timeout: float = 1800.0):
        self.room_id = room_id
        self._queue: queue.Queue = queue.Queue()
        self._resources: dict[str, Any] = {}
        self._cleanups: dict[str, Callable] = {}
        self._running = True
        self._last_active: float = time.time()
        self._idle_timeout = idle_timeout
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name=f"room-session-{room_id[:8]}",
        )
        self._thread.start()
        logger.info(f"[RoomSession] Created for room {room_id}")

    @property
    def is_idle(self) -> bool:
        return time.time() - self._last_active > self._idle_timeout

    def _run(self):
        while self._running:
            try:
                item = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            if item is None:
                break
            fn, future = item
            try:
                self._last_active = time.time()
                result = fn(self._resources)
                if not future.done():
                    future.set_result(result)
            except Exception as e:
                if not future.done():
                    future.set_exception(e)
        self._cleanup()

    def submit(self, fn: Callable[[dict], Any], timeout: float = 30.0) -> Any:
        if not self._running:
            raise RuntimeError(f"RoomSession {self.room_id} is shut down")
        future = Future()
        self._queue.put((fn, future))
        return future.result(timeout=timeout)

    async def submit_async(self, fn: Callable[[dict], Any], timeout: float = 30.0) -> Any:
        if not self._running:
            raise RuntimeError(f"RoomSession {self.room_id} is shut down")
        future: Future = Future()
        self._queue.put((fn, future))
        awaitable = asyncio.wrap_future(future)
        return await asyncio.wait_for(awaitable, timeout=timeout)

    def register_cleanup(self, name: str, cleanup_fn: Callable):
        self._cleanups[name] = cleanup_fn

    def _cleanup(self):
        for name, resource in self._resources.items():
            cleanup_fn = self._cleanups.get(name)
            if cleanup_fn:
                try:
                    cleanup_fn(resource)
                except Exception as e:
                    logger.error(f"[RoomSession] Error cleaning up {name} in room {self.room_id}: {e}")
            elif hasattr(resource, "close"):
                try:
                    resource.close()
                except Exception as e:
                    logger.error(f"[RoomSession] Error closing {name} in room {self.room_id}: {e}")
        self._resources.clear()
        logger.info(f"[RoomSession] Cleaned up resources for room {self.room_id}")

    def shutdown(self):
        self._running = False
        self._queue.put(None)
        self._thread.join(timeout=5.0)


class RoomSessionManager:
    _instance: Optional["RoomSessionManager"] = None

    def __init__(self, idle_timeout: float = 1800.0):
        self._sessions: dict[str, RoomSession] = {}
        self._idle_timeout = idle_timeout
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "RoomSessionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_session(self, room_id: str) -> RoomSession:
        with self._lock:
            if room_id not in self._sessions:
                self._sessions[room_id] = RoomSession(room_id, self._idle_timeout)
            return self._sessions[room_id]

    def cleanup_room(self, room_id: str):
        with self._lock:
            session = self._sessions.pop(room_id, None)
        if session:
            session.shutdown()
            logger.info(f"[RoomSessionManager] Cleaned up session for room {room_id}")

    def cleanup_idle(self):
        with self._lock:
            idle_rooms = [rid for rid, session in self._sessions.items() if session.is_idle]
        for rid in idle_rooms:
            self.cleanup_room(rid)
            logger.info(f"[RoomSessionManager] Cleaned up idle session for room {rid}")

    def shutdown_all(self):
        with self._lock:
            rooms = list(self._sessions.keys())
        for rid in rooms:
            self.cleanup_room(rid)
