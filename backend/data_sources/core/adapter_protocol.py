from __future__ import annotations

from typing import Protocol

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class SourceAdapter(Protocol):
    manifest: SourceManifest

    def healthcheck(self) -> SourceHealth:
        ...

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        ...

    def fetch(self, item: SourceItem) -> SourcePayload:
        ...
