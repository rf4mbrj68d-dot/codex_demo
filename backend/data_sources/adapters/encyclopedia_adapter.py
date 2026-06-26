from __future__ import annotations

from backend.company_profile.wikipedia_client import EncyclopediaClient
from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class EncyclopediaAdapter:
    def __init__(self, client: EncyclopediaClient):
        self.client = client
        self.manifest = SourceManifest.from_dict({
            "source_id": "encyclopedia",
            "source_name": "Wikipedia / 百度百科",
            "enabled": True,
            "markets": ["ALL", "US", "CN", "HK"],
            "source_types": ["encyclopedia"],
            "capabilities": ["search", "fetch", "fetch_encyclopedia"],
            "ttl": {"encyclopedia": "45d"},
            "priority": 40,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("encyclopedia", "ready", "百科适配器可用")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        context = self.client.fetch_company_context(request.company)
        if not context:
            return []
        return [self._item(request.company, context)]

    def fetch(self, item: SourceItem) -> SourcePayload:
        text = item.metadata.get("summary") or ""
        return SourcePayload(item=item, content_type="text/plain", raw_bytes=text.encode("utf-8"), raw_text=text, structured_data=item.metadata)

    def fetch_encyclopedia(self, company: dict) -> dict | None:
        return self.client.fetch_company_context(company)

    def _item(self, company: dict, context: dict) -> SourceItem:
        return SourceItem(
            source_id="encyclopedia",
            source_name=context.get("source_type") or self.manifest.source_name,
            source_type="encyclopedia",
            market=company.get("market", "ALL"),
            title=context.get("title") or company.get("name", ""),
            company_hint=company,
            source_url=context.get("url"),
            external_id="ENC-%s-%s" % (company.get("id"), context.get("source_type") or "encyclopedia"),
            document_type=context.get("source_type") or "encyclopedia",
            period="reference",
            metadata=context,
        )
