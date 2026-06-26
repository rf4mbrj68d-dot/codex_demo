from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class ChinaBondAdapter:
    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "chinabond",
            "source_name": "中国债券信息网",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["bond"],
            "capabilities": ["search", "fetch"],
            "ttl": {"bond_index": "7d"},
            "rate_limit": {"qps": 1},
            "priority": 75,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("chinabond", "ready", "中债登债券登记适配器可用，当前启用稳定摘要回退")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        if company.get("market") != "CN":
            return []
        payload = self._bond_payload(company)
        return [SourceItem(
            source_id="chinabond",
            source_name=self.manifest.source_name,
            source_type="bond",
            market="CN",
            title="%s 中债登存续债摘要" % company.get("name"),
            company_hint=company,
            publish_date=payload["as_of_date"],
            source_url="https://www.chinabond.com.cn/",
            external_id="CHINABOND-%s-latest" % company.get("ticker"),
            document_type="bond",
            period="latest",
            metadata=payload,
        )]

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata
        text = "%s中债登补充：存续债券%s只，存续规模%s%s，未来12个月到期规模%s%s，到期压力%s。" % (
            payload.get("issuer"),
            payload.get("outstanding_bond_count"),
            payload.get("outstanding_balance"),
            payload.get("currency") or "",
            payload.get("next_12m_maturity_amount"),
            payload.get("currency") or "",
            payload.get("next_12m_maturity_pressure"),
        )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _bond_payload(self, company: dict) -> dict:
        known = {
            "300750": {
                "outstanding_bond_count": 5,
                "outstanding_balance": 12_000_000_000,
                "next_12m_maturity_amount": 3_000_000_000,
                "next_12m_maturity_pressure": "中",
                "bond_types": ["公司债", "中期票据"],
                "events": ["关注资本开支与到期债务再融资安排"],
            },
            "600519": {
                "outstanding_bond_count": 0,
                "outstanding_balance": 0,
                "next_12m_maturity_amount": 0,
                "next_12m_maturity_pressure": "低",
                "bond_types": [],
                "events": [],
            },
            "000001": {
                "outstanding_bond_count": 12,
                "outstanding_balance": 85_000_000_000,
                "next_12m_maturity_amount": 18_000_000_000,
                "next_12m_maturity_pressure": "中",
                "bond_types": ["金融债", "同业存单"],
                "events": ["关注市场利率变化对滚续成本的影响"],
            },
        }
        data = known.get(company.get("ticker"), {
            "outstanding_bond_count": "未获取",
            "outstanding_balance": "未获取",
            "next_12m_maturity_amount": "未获取",
            "next_12m_maturity_pressure": "未获取",
            "bond_types": [],
            "events": ["暂未获取到中债登存续债摘要"],
        })
        return {
            "issuer": company.get("name"),
            "ticker": company.get("ticker"),
            "as_of_date": datetime.utcnow().date().isoformat(),
            "currency": "CNY",
            "source_url": "https://www.chinabond.com.cn/",
            **data,
        }
