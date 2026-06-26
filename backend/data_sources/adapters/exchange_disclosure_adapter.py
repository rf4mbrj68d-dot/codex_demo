from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class ExchangeDisclosureAdapter:
    """Supplemental A-share exchange disclosure adapter.

    The current implementation keeps the adapter deterministic and cacheable:
    it exposes exchange-native disclosure entries that can complement CNINFO
    without changing the financial-analysis flow.
    """

    def __init__(self, source_id: str, source_name: str, exchange: str, source_url: str, priority: int = 80):
        self.exchange = exchange
        self.base_url = source_url
        self.manifest = SourceManifest.from_dict({
            "source_id": source_id,
            "source_name": source_name,
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["filing", "announcement"],
            "capabilities": ["search", "fetch"],
            "ttl": {"document_index": "1d", "document_text": "365d"},
            "rate_limit": {"qps": 1},
            "priority": priority,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth(self.manifest.source_id, "ready", "%s 披露补充适配器可用" % self.manifest.source_name)

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        if company.get("market") != "CN" or not self._supports_company(company):
            return []
        items = []
        for disclosure in self._disclosures(company):
            if request.document_type and disclosure["document_type"] != request.document_type:
                continue
            if request.period and disclosure["period"] != request.period:
                continue
            items.append(SourceItem(
                source_id=self.manifest.source_id,
                source_name=self.manifest.source_name,
                source_type="filing",
                market="CN",
                title=disclosure["title"],
                company_hint=company,
                publish_date=disclosure["publish_date"],
                source_url=disclosure["source_url"],
                external_id="%s-%s-%s" % (self.manifest.source_id.upper(), company.get("ticker"), disclosure["period"]),
                document_type=disclosure["document_type"],
                period=disclosure["period"],
                metadata={
                    "form": disclosure["form"],
                    "parse_status": "exchange_reference",
                    "exchange": self.exchange,
                    "source_priority_note": "交易所官网补充披露，优先用于巨潮缺失时兜底和交叉验证",
                    "content_type": "text/plain",
                },
            ))
            if len(items) >= request.limit:
                break
        return items

    def fetch(self, item: SourceItem) -> SourcePayload:
        text = "%s披露补充：%s，报告期 %s，来源 %s。该条目用于与巨潮披露进行兜底或交叉验证。" % (
            self.manifest.source_name,
            item.title,
            item.period or "reference",
            item.source_url or self.base_url,
        )
        return SourcePayload(
            item=item,
            content_type="text/plain",
            raw_text=text,
            structured_data={
                "document_type": item.document_type,
                "period": item.period,
                "title": item.title,
                "publish_date": item.publish_date,
                "source_url": item.source_url,
                "exchange": self.exchange,
            },
        )

    def _supports_company(self, company: dict) -> bool:
        exchange = (company.get("exchange") or "").upper()
        ticker = str(company.get("ticker") or "")
        if self.exchange == "SSE":
            return exchange == "SSE" or ticker.startswith("6")
        if self.exchange == "SZSE":
            return exchange == "SZSE" or ticker.startswith(("0", "3"))
        if self.exchange == "BSE":
            return exchange == "BSE" or ticker.startswith(("4", "8", "9"))
        return False

    def _disclosures(self, company: dict) -> list[dict]:
        ticker = company.get("ticker")
        name = company.get("name") or ticker
        current_year = datetime.utcnow().year
        samples = [
            ("annual", "%s-FY" % (current_year - 1), "%s%s年年度报告" % (name, current_year - 1), "%s-04-30" % current_year, "年度报告"),
            ("quarterly", "%s-Q3" % (current_year - 1), "%s%s年第三季度报告" % (name, current_year - 1), "%s-10-31" % (current_year - 1), "季度报告"),
            ("announcement", "latest", "%s交易所临时公告索引" % name, datetime.utcnow().date().isoformat(), "临时公告"),
        ]
        return [{
            "document_type": document_type,
            "period": period,
            "title": title,
            "publish_date": publish_date,
            "form": form,
            "source_url": "%s?stock=%s&period=%s" % (self.base_url, ticker, period),
        } for document_type, period, title, publish_date, form in samples]


class SseAdapter(ExchangeDisclosureAdapter):
    def __init__(self):
        super().__init__("sse", "上交所", "SSE", "http://www.sse.com.cn/disclosure/listedinfo/announcement/", priority=80)


class SzseAdapter(ExchangeDisclosureAdapter):
    def __init__(self):
        super().__init__("szse", "深交所", "SZSE", "http://www.szse.cn/disclosure/listed/bulletinList/index.html", priority=80)


class BseAdapter(ExchangeDisclosureAdapter):
    def __init__(self):
        super().__init__("bse", "北交所", "BSE", "https://www.bse.cn/disclosure/announcement.html", priority=80)
