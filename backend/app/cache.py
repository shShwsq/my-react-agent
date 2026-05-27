import time
from typing import Any, Optional
from threading import Lock


class SimpleCache:
    def __init__(self, default_timeout: int = 3600):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = Lock()
        self._default_timeout = default_timeout
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            value, expires_at = self._cache[key]
            if time.time() > expires_at:
                del self._cache[key]
                return None
            return value
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        with self._lock:
            expires_at = time.time() + (timeout or self._default_timeout)
            self._cache[key] = (value, expires_at)
            return True
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            return True
    
    def clear(self) -> bool:
        with self._lock:
            self._cache.clear()
            return True
    
    def has(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            _, expires_at = self._cache[key]
            if time.time() > expires_at:
                del self._cache[key]
                return False
            return True


cache = SimpleCache(default_timeout=3600)
