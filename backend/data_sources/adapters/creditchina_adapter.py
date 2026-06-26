from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class CreditChinaAdapter:
    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "creditchina",
            "source_name": "信用中国",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["credit_event"],
            "capabilities": ["search", "fetch"],
            "ttl": {"credit_event_index": "7d"},
            "rate_limit": {"qps": 1},
            "priority": 90,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("creditchina", "ready", "信用中国风险事件适配器可用，当前启用稳定摘要回退")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        if company.get("market") != "CN":
            return []
        payloads = self._events(company)
        return [SourceItem(
            source_id="creditchina",
            source_name=self.manifest.source_name,
            source_type="credit_event",
            market="CN",
            title=payload["title"],
            company_hint=company,
            publish_date=payload["event_date"],
            source_url=payload["source_url"],
            external_id="CREDITCHINA-%s-%s" % (company.get("ticker"), index),
            document_type="credit_event",
            period="latest",
            metadata=payload,
        ) for index, payload in enumerate(payloads[: request.limit], start=1)]

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata
        text = "%s信用风险补充：%s，事件级别%s，事件日期%s。%s 来源：%s" % (
            payload.get("subject_name"),
            payload.get("title"),
            payload.get("event_level"),
            payload.get("event_date"),
            payload.get("description"),
            payload.get("source_url"),
        )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _events(self, company: dict) -> list[dict]:
        ticker = company.get("ticker")
        today = datetime.utcnow().date().isoformat()
        known = {
            "000001": [{
                "event_type": "regulatory_notice",
                "event_level": "low",
                "title": "未发现重大失信或严重违法公开摘要",
                "description": "演示环境未获取到该主体近期重大失信、严重违法或高等级行政处罚摘要。",
            }],
            "600519": [{
                "event_type": "no_material_event",
                "event_level": "low",
                "title": "未发现重大失信或严重违法公开摘要",
                "description": "演示环境未获取到该主体近期重大失信、严重违法或高等级行政处罚摘要。",
            }],
            "300750": [{
                "event_type": "no_material_event",
                "event_level": "low",
                "title": "未发现重大失信或严重违法公开摘要",
                "description": "演示环境未获取到该主体近期重大失信、严重违法或高等级行政处罚摘要。",
            }],
        }
        records = known.get(ticker, [{
            "event_type": "unknown",
            "event_level": "unknown",
            "title": "信用风险事件摘要待补充",
            "description": "暂未获取到信用中国公开事件摘要，需后续联网刷新或人工复核。",
        }])
        result = []
        for record in records:
            result.append({
                "subject_name": company.get("name"),
                "ticker": ticker,
                "event_date": today,
                "authority": "信用中国",
                "source_url": "https://www.creditchina.gov.cn/",
                **record,
            })
        return result
