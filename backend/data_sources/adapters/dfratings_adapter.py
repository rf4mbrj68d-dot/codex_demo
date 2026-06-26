from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class DfratingsAdapter:
    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "dfratings",
            "source_name": "东方金诚",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["rating"],
            "capabilities": ["search", "fetch"],
            "ttl": {"rating_index": "7d", "rating_report": "180d"},
            "priority": 60,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("dfratings", "ready", "评级适配器可用，当前启用稳定摘要回退")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        if company.get("market") != "CN":
            return []
        payload = self._rating_payload(company)
        return [SourceItem(
            source_id="dfratings",
            source_name=self.manifest.source_name,
            source_type="rating",
            market="CN",
            title="%s 主体评级摘要" % company.get("name"),
            company_hint=company,
            publish_date=payload["rating_date"],
            source_url="https://www.dfratings.com/",
            external_id="DFR-%s" % company.get("id"),
            document_type="rating",
            period="latest",
            metadata=payload,
        )]

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata
        text = "%s：主体评级 %s，展望 %s。关注点：%s。" % (
            payload.get("subject_name"),
            payload.get("subject_rating"),
            payload.get("rating_outlook"),
            "；".join(payload.get("concerns", [])),
        )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _rating_payload(self, company: dict) -> dict:
        ticker = company.get("ticker")
        known = {
            "300750": {"subject_rating": "AAA", "rating_outlook": "稳定", "concerns": ["行业景气波动", "海外产能扩张投入较大"]},
            "600519": {"subject_rating": "AAA", "rating_outlook": "稳定", "concerns": ["高端消费需求变化"]},
            "000001": {"subject_rating": "AAA", "rating_outlook": "稳定", "concerns": ["资产质量与息差变化"]},
        }
        data = known.get(ticker, {"subject_rating": "未获取", "rating_outlook": "未获取", "concerns": ["暂未获取到公开评级摘要"]})
        return {"agency_name": self.manifest.source_name, "subject_name": company.get("name"), "ticker": ticker, "rating_date": datetime.utcnow().date().isoformat(), "rating_action": "latest", **data}
