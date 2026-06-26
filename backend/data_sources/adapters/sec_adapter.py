from __future__ import annotations

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest
from backend.services.sec_client import SecClient


class SecAdapter:
    def __init__(self, client: SecClient):
        self.client = client
        self.manifest = SourceManifest.from_dict({
            "source_id": "sec",
            "source_name": "SEC EDGAR",
            "enabled": True,
            "markets": ["US"],
            "source_types": ["company", "filing", "financial_dataset"],
            "capabilities": ["search", "fetch", "search_companies", "resolve_company", "top_companies", "fetch_financial_dataset"],
            "rate_limit": {"qps": 8},
            "ttl": {"document_index": "1d", "document_text": "365d", "financial_dataset": "7d"},
            "priority": 100,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("sec", "ready", "SEC adapter ready")

    def search_companies(self, query: str) -> list[dict]:
        return self.client.search_companies(query)

    def resolve_company(self, query: str) -> dict:
        return self.client.resolve_company(query)

    def top_companies(self, limit: int = 80) -> list[dict]:
        return [
            {"id": "US-AAPL", "ticker": "AAPL", "name": "Apple Inc.", "market": "US", "industry": "科技"},
            {"id": "US-MSFT", "ticker": "MSFT", "name": "Microsoft", "market": "US", "industry": "科技"},
            {"id": "US-NVDA", "ticker": "NVDA", "name": "NVIDIA", "market": "US", "industry": "科技"},
            {"id": "US-GOOGL", "ticker": "GOOGL", "name": "Alphabet", "market": "US", "industry": "科技"},
            {"id": "US-META", "ticker": "META", "name": "Meta Platforms", "market": "US", "industry": "科技"},
            {"id": "US-BIDU", "ticker": "BIDU", "name": "Baidu, Inc.", "market": "US", "industry": "互联网"},
            {"id": "US-TSLA", "ticker": "TSLA", "name": "Tesla", "market": "US", "industry": "汽车"},
            {"id": "US-AMZN", "ticker": "AMZN", "name": "Amazon", "market": "US", "industry": "互联网零售"},
            {"id": "US-JPM", "ticker": "JPM", "name": "JPMorgan Chase", "market": "US", "industry": "金融"},
        ][:limit]

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        if request.source_type not in {"filing", "annual", "quarterly", "prospectus"}:
            return []
        cik = request.company.get("cik")
        if not cik:
            return []
        items = []
        for source in self.client.list_filing_documents(cik):
            form = source.get("form") or "SEC filing"
            document_type = "annual" if form in {"10-K", "20-F"} else ("prospectus" if form in {"S-1", "F-1"} else "quarterly")
            if request.document_type and document_type != request.document_type:
                continue
            year = str(source.get("report_date") or source.get("filing_date") or "")[:4]
            period = "%s-FY" % year if document_type == "annual" else "%s-PROSPECTUS" % year
            if request.period and request.period != period:
                continue
            items.append(SourceItem(
                source_id="sec",
                source_name=self.manifest.source_name,
                source_type="filing",
                market="US",
                title="%s %s %s" % (request.company.get("name"), period, form),
                company_hint=request.company,
                publish_date=source.get("filing_date"),
                source_url=source.get("url"),
                external_id="SEC-%s-%s-%s" % (request.company.get("ticker"), period, source.get("accession")),
                document_type=document_type,
                period=period,
                metadata={**source, "form": form, "report_type": document_type, "parse_status": "source_adapter"},
            ))
            if len(items) >= request.limit:
                break
        return sorted(items, key=lambda item: item.period or "", reverse=True)

    def fetch(self, item: SourceItem) -> SourcePayload:
        content = self.client.download_filing_html(item.source_url or "")
        text = self.client.extract_filing_text_from_html(content)
        return SourcePayload(item=item, content_type="text/html", raw_bytes=content, raw_text=text)

    def fetch_financial_dataset(self, company: dict, periods=None, period_type: str = "annual") -> dict:
        return self.client.fetch_financial_dataset(company["cik"])
