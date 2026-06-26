from __future__ import annotations

from backend.data_sources.ashare_source import AShareSource
from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class CninfoAdapter:
    def __init__(self, source: AShareSource):
        self.source = source
        self.manifest = SourceManifest.from_dict({
            "source_id": "cninfo",
            "source_name": "CNINFO",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["company", "filing", "announcement", "financial_dataset"],
            "capabilities": ["search", "fetch", "search_companies", "resolve_company", "top_companies", "fetch_financial_dataset"],
            "rate_limit": {"qps": 1},
            "ttl": {"document_index": "1d", "document_text": "365d", "financial_dataset": "30d"},
            "priority": 100,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("cninfo", "ready", "巨潮适配器可用")

    def search_companies(self, query: str) -> list[dict]:
        return self.source.search_companies(query)

    def resolve_company(self, query: str) -> dict:
        return self.source.resolve_company(query)

    def top_companies(self, limit: int = 80) -> list[dict]:
        return self.source.top_companies(limit=limit)

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        if request.source_type not in {"filing", "announcement", "annual", "quarterly", "prospectus"}:
            return []
        reports = self.source.list_reports(request.company)
        try:
            reports.extend(self.source.cninfo.list_prospectuses(request.company)[:1])
        except Exception:
            pass
        items = []
        for report in reports:
            document_type = report.get("report_type") or "annual"
            if request.document_type and document_type != request.document_type:
                continue
            if request.period and report.get("period") != request.period:
                continue
            items.append(SourceItem(
                source_id="cninfo",
                source_name=self.manifest.source_name,
                source_type="filing",
                market="CN",
                title=report.get("title") or "%s %s" % (request.company.get("name"), report.get("period")),
                company_hint=request.company,
                publish_date=report.get("publish_date"),
                source_url=report.get("source_url"),
                external_id=report.get("id"),
                document_type=document_type,
                period=report.get("period"),
                metadata={**report, "source_platform": "CNINFO", "market": "CN"},
            ))
            if len(items) >= request.limit:
                break
        return items

    def fetch(self, item: SourceItem) -> SourcePayload:
        raw = self.source.cninfo.download_pdf(item.source_url or "")
        text = self.source.cninfo.extract_pdf_text_from_bytes(raw)
        return SourcePayload(item=item, content_type="application/pdf", raw_bytes=raw, raw_text=text)

    def fetch_financial_dataset(self, company: dict, periods=None, period_type: str = "annual") -> dict:
        return self.source.fetch_financial_dataset(company, periods=periods, period_type=period_type)
