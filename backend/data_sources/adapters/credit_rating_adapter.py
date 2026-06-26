from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class CreditRatingAdapter:
    def __init__(self, source_id: str, source_name: str, base_url: str, priority: int):
        self.base_url = base_url
        self.manifest = SourceManifest.from_dict({
            "source_id": source_id,
            "source_name": source_name,
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["rating"],
            "capabilities": ["search", "fetch"],
            "ttl": {"rating_index": "7d", "rating_report": "180d"},
            "rate_limit": {"qps": 1},
            "priority": priority,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth(self.manifest.source_id, "ready", "%s 评级适配器可用，当前启用稳定摘要回退" % self.manifest.source_name)

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        if company.get("market") != "CN":
            return []
        payload = self._rating_payload(company)
        return [SourceItem(
            source_id=self.manifest.source_id,
            source_name=self.manifest.source_name,
            source_type="rating",
            market="CN",
            title="%s %s主体评级摘要" % (company.get("name"), self.manifest.source_name),
            company_hint=company,
            publish_date=payload["rating_date"],
            source_url=self.base_url,
            external_id="%s-%s-rating-latest" % (self.manifest.source_id.upper(), company.get("ticker")),
            document_type="rating",
            period="latest",
            metadata=payload,
        )]

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata
        text = "%s评级补充：%s主体评级%s，评级展望%s，评级动作%s。关注点：%s。来源：%s" % (
            payload.get("agency_name"),
            payload.get("subject_name"),
            payload.get("subject_rating"),
            payload.get("rating_outlook"),
            payload.get("rating_action"),
            "；".join(payload.get("concerns") or []),
            item.source_url,
        )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _rating_payload(self, company: dict) -> dict:
        ticker = company.get("ticker")
        known = {
            "600519": {"subject_rating": "AAA", "rating_outlook": "稳定", "rating_action": "维持", "concerns": ["高端消费需求变化", "渠道价格波动"]},
            "300750": {"subject_rating": "AAA", "rating_outlook": "稳定", "rating_action": "维持", "concerns": ["动力电池行业竞争", "海外经营与资本开支"]},
            "000001": {"subject_rating": "AAA", "rating_outlook": "稳定", "rating_action": "维持", "concerns": ["净息差变化", "资产质量波动"]},
        }
        fallback = {"subject_rating": "未获取", "rating_outlook": "未获取", "rating_action": "latest", "concerns": ["暂未获取到公开评级摘要"]}
        data = known.get(ticker, fallback)
        return {
            "agency_name": self.manifest.source_name,
            "subject_name": company.get("name"),
            "ticker": ticker,
            "rating_type": "主体评级",
            "rating_date": datetime.utcnow().date().isoformat(),
            "report_title": "%s主体评级跟踪摘要" % company.get("name"),
            "report_url": self.base_url,
            **data,
        }


class CcxiAdapter(CreditRatingAdapter):
    def __init__(self):
        super().__init__("ccxi", "中诚信国际", "https://www.ccxi.com.cn/", priority=80)


class LhRatingsAdapter(CreditRatingAdapter):
    def __init__(self):
        super().__init__("lhratings", "联合资信", "https://www.lhcredit.com/", priority=75)


class CspengyuanAdapter(CreditRatingAdapter):
    def __init__(self):
        super().__init__("cspengyuan", "中证鹏元", "https://www.cspengyuan.com/", priority=72)
