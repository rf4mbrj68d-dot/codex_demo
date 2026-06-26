from __future__ import annotations

import time
from threading import RLock


class SimpleRateLimiter:
    def __init__(self, qps: float = 1.0):
        self.min_interval = 0 if qps <= 0 else 1.0 / qps
        self._last = 0.0
        self._lock = RLock()

    def wait(self) -> None:
        if self.min_interval <= 0:
            return
        with self._lock:
            elapsed = time.time() - self._last
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self._last = time.time()
