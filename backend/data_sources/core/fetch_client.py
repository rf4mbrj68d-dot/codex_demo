from __future__ import annotations

import requests

from backend.data_sources.core.rate_limiter import SimpleRateLimiter


class FetchClient:
    def __init__(self, qps: float = 1.0, trust_env: bool = True):
        self.session = requests.Session()
        self.session.trust_env = trust_env
        self.limiter = SimpleRateLimiter(qps=qps)

    def get_bytes(self, url: str, headers: dict | None = None, timeout: int = 20) -> bytes:
        self.limiter.wait()
        response = self.session.get(url, headers=headers or {}, timeout=timeout)
        response.raise_for_status()
        return response.content

    def get_json(self, url: str, headers: dict | None = None, timeout: int = 20) -> dict:
        self.limiter.wait()
        response = self.session.get(url, headers=headers or {}, timeout=timeout)
        response.raise_for_status()
        return response.json()
