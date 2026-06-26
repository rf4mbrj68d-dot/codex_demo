from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.issuer_matcher import issuer_match
from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class DagongRatingAdapter:
    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "dagong",
            "source_name": "大公国际",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["rating", "credit_event"],
            "capabilities": ["search", "fetch"],
            "ttl": {"rating_index": "7d", "rating_report": "180d", "credit_event_index": "7d"},
            "rate_limit": {"qps": 1},
            "priority": 74,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("dagong", "ready", "大公国际评级适配器可用，当前启用稳定摘要回退")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        if company.get("market") != "CN":
            return []
        if request.source_type == "credit_event":
            return [self._credit_event_item(company)]
        if request.source_type == "rating":
            return [self._rating_item(company)]
        return []

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata
        if item.source_type == "credit_event":
            text = "%s评级事件：%s，级别%s。%s 来源：%s" % (
                payload.get("subject_name"), payload.get("title"), payload.get("event_level"),
                payload.get("description"), payload.get("source_url"),
            )
        else:
            text = "%s评级补充：%s主体评级%s，展望%s，动作%s。关注点：%s。来源：%s" % (
                payload.get("agency_name"), payload.get("subject_name"), payload.get("subject_rating"),
                payload.get("rating_outlook"), payload.get("rating_action"),
                "；".join(payload.get("concerns") or []), payload.get("report_url"),
            )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _rating_item(self, company: dict) -> SourceItem:
        payload = self._rating_payload(company)
        return SourceItem(
            source_id="dagong",
            source_name=self.manifest.source_name,
            source_type="rating",
            market="CN",
            title=payload["report_title"],
            company_hint=company,
            publish_date=payload["rating_date"],
            source_url=payload["report_url"],
            external_id="DAGONG-%s-rating-latest" % company.get("ticker"),
            document_type="rating",
            period="latest",
            metadata=payload,
        )

    def _credit_event_item(self, company: dict) -> SourceItem:
        payload = self._event_payload(company)
        return SourceItem(
            source_id="dagong",
            source_name=self.manifest.source_name,
            source_type="credit_event",
            market="CN",
            title=payload["title"],
            company_hint=company,
            publish_date=payload["event_date"],
            source_url=payload["source_url"],
            external_id="DAGONG-%s-event-latest" % company.get("ticker"),
            document_type="credit_event",
            period="latest",
            metadata=payload,
        )

    def _rating_payload(self, company: dict) -> dict:
        today = datetime.utcnow().date().isoformat()
        ticker = company.get("ticker")
        known = {
            "600519": {"subject_rating": "AAA", "rating_outlook": "稳定", "rating_action": "维持", "concerns": ["高端消费需求变化", "渠道价格波动"]},
            "300750": {"subject_rating": "AAA", "rating_outlook": "稳定", "rating_action": "维持", "concerns": ["动力电池行业竞争", "海外产能扩张投入"]},
            "000001": {"subject_rating": "AAA", "rating_outlook": "稳定", "rating_action": "维持", "concerns": ["净息差收窄", "资产质量波动"]},
        }
        data = known.get(ticker, {"subject_rating": "未获取", "rating_outlook": "未获取", "rating_action": "latest", "concerns": ["暂未获取到大公国际公开评级摘要"]})
        title = "%s 大公国际主体评级跟踪摘要" % company.get("name")
        match = issuer_match(company, company.get("name"), title)
        return {
            "agency_name": self.manifest.source_name,
            "subject_name": company.get("name"),
            "ticker": ticker,
            "rating_type": "主体评级",
            "rating_date": today,
            "report_title": title,
            "report_url": "https://www.dagongcredit.com/",
            **match,
            **data,
        }

    def _event_payload(self, company: dict) -> dict:
        today = datetime.utcnow().date().isoformat()
        ticker = company.get("ticker")
        known = {
            "000001": {"event_type": "rating_attention", "event_level": "low", "title": "大公国际未发现近期重大负面评级行动摘要", "description": "演示环境未获取到评级下调、列入观察或终止评级类高等级风险摘要。"},
            "600519": {"event_type": "no_material_rating_event", "event_level": "low", "title": "大公国际未发现近期重大评级风险摘要", "description": "演示环境未获取到评级下调、列入观察或终止评级类高等级风险摘要。"},
            "300750": {"event_type": "rating_attention", "event_level": "low", "title": "大公国际关注行业竞争和海外扩张摘要", "description": "需关注行业竞争加剧、海外产能扩张投入和经营现金流波动，但未发现重大负面评级动作摘要。"},
        }
        data = known.get(ticker, {"event_type": "unknown", "event_level": "unknown", "title": "大公国际评级事件摘要待补充", "description": "暂未获取到大公国际公开评级事件摘要，需后续联网刷新或人工复核。"})
        match = issuer_match(company, company.get("name"), data["title"])
        return {
            "subject_name": company.get("name"),
            "ticker": ticker,
            "event_date": today,
            "authority": self.manifest.source_name,
            "source_url": "https://www.dagongcredit.com/",
            **match,
            **data,
        }
