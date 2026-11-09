"""Límite de peticiones por IP en memoria (ventana deslizante). Suficiente para una sola instancia."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    def __init__(self, per_minute: int, per_day: int) -> None:
        self.limits = ((60.0, per_minute), (86_400.0, per_day))
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.limits[-1][0]:
                hits.popleft()
            for window, limit in self.limits:
                if sum(1 for t in hits if now - t <= window) >= limit:
                    return False
            hits.append(now)
            # Limpieza ocasional para no crecer sin fin
            if len(self._hits) > 10_000:
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]
            return True
