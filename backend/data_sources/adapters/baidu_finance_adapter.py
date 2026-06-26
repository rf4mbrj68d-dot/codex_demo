from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class BaiduFinanceAdapter:
    """Quote adapter with a deterministic offline fallback for demo stability.

    The adapter boundary is real: a production implementation can replace
    `_quote_payload` with a licensed quote API or page parser without touching
    DataService, KnowledgeRepository, or agents.
    """

    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "baidu_finance",
            "source_name": "百度股市行情",
            "enabled": True,
            "markets": ["US", "CN", "HK"],
            "source_types": ["quote"],
            "capabilities": ["search", "fetch"],
            "ttl": {"quote": "30m"},
            "priority": 50,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("baidu_finance", "ready", "行情适配器可用，当前启用离线稳定回退")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        return [SourceItem(
            source_id="baidu_finance",
            source_name=self.manifest.source_name,
            source_type="quote",
            market=company.get("market", ""),
            title="%s 行情快照" % (company.get("name") or company.get("ticker")),
            company_hint=company,
            publish_date=datetime.utcnow().date().isoformat(),
            source_url="https://finance.baidu.com/",
            external_id="QUOTE-%s" % company.get("id"),
            document_type="quote",
            period="latest",
            metadata=self._quote_payload(company),
        )]

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata or self._quote_payload(item.company_hint)
        text = "%s 当前行情：价格 %s，市值 %s，PE %s，PB %s，涨跌幅 %s。" % (
            item.company_hint.get("name") or item.company_hint.get("ticker"),
            payload.get("price", "待补充"),
            payload.get("market_cap", "待补充"),
            payload.get("pe", "待补充"),
            payload.get("pb", "待补充"),
            payload.get("change_pct", "待补充"),
        )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _quote_payload(self, company: dict) -> dict:
        ticker = (company.get("ticker") or "").upper()
        samples = {
            "AAPL": {"price": 201.50, "currency": "USD", "market_cap": "3.05T USD", "pe": 29.4, "pb": 43.1, "change_pct": "0.8%"},
            "300750": {"price": 246.10, "currency": "CNY", "market_cap": "1.08T CNY", "pe": 18.7, "pb": 4.9, "change_pct": "1.2%"},
            "00700": {"price": 382.40, "currency": "HKD", "market_cap": "3.58T HKD", "pe": 18.9, "pb": 3.5, "change_pct": "0.6%"},
        }
        data = samples.get(ticker, {"price": "待补充", "currency": "", "market_cap": "待补充", "pe": "待补充", "pb": "待补充", "change_pct": "待补充"})
        return {"ticker": ticker, "market": company.get("market"), "trade_date": datetime.utcnow().date().isoformat(), **data}
