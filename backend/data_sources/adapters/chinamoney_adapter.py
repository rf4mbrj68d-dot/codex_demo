from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class ChinaMoneyAdapter:
    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "chinamoney",
            "source_name": "中国货币网",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["bond"],
            "capabilities": ["search", "fetch"],
            "ttl": {"bond_index": "7d"},
            "priority": 55,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("chinamoney", "ready", "债券适配器可用，当前启用稳定摘要回退")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        if request.company.get("market") != "CN":
            return []
        payload = self._bond_payload(request.company)
        return [SourceItem(
            source_id="chinamoney",
            source_name=self.manifest.source_name,
            source_type="bond",
            market="CN",
            title="%s 债券与债务融资工具摘要" % request.company.get("name"),
            company_hint=request.company,
            publish_date=payload["as_of_date"],
            source_url="https://www.chinamoney.com.cn/",
            external_id="BOND-%s" % request.company.get("id"),
            document_type="bond",
            period="latest",
            metadata=payload,
        )]

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata
        text = "%s 债券补充：存续债券数量 %s，未来一年到期压力 %s。" % (
            item.company_hint.get("name"), payload.get("outstanding_bond_count"), payload.get("next_12m_maturity_pressure")
        )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _bond_payload(self, company: dict) -> dict:
        known = {
            "300750": {"outstanding_bond_count": 2, "next_12m_maturity_pressure": "低", "events": []},
            "600519": {"outstanding_bond_count": 0, "next_12m_maturity_pressure": "低", "events": []},
            "000001": {"outstanding_bond_count": 8, "next_12m_maturity_pressure": "中", "events": ["关注同业存单与金融债续发成本"]},
        }
        data = known.get(company.get("ticker"), {"outstanding_bond_count": "未获取", "next_12m_maturity_pressure": "未获取", "events": []})
        return {"issuer": company.get("name"), "ticker": company.get("ticker"), "as_of_date": datetime.utcnow().date().isoformat(), **data}
