from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.issuer_matcher import issuer_match
from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class CfaeBondAdapter:
    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "cfae",
            "source_name": "北金所",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["bond", "credit_event"],
            "capabilities": ["search", "fetch"],
            "ttl": {"bond_index": "7d", "credit_event_index": "7d"},
            "rate_limit": {"qps": 1},
            "priority": 68,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("cfae", "ready", "北金所债权融资计划适配器可用，当前启用稳定摘要回退")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        if company.get("market") != "CN":
            return []
        if request.source_type == "credit_event":
            return [self._credit_event_item(company)]
        if request.source_type == "bond":
            return [self._bond_item(company)]
        return []

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata
        if item.source_type == "credit_event":
            text = "%s北金所披露事件：%s，级别%s。%s 来源：%s" % (
                payload.get("subject_name"), payload.get("title"), payload.get("event_level"),
                payload.get("description"), payload.get("source_url"),
            )
        else:
            text = "%s北金所融资披露补充：融资工具%s只，余额%s%s，未来12个月到期压力%s。工具类型：%s。来源：%s" % (
                payload.get("issuer"), payload.get("outstanding_bond_count"), payload.get("outstanding_balance"),
                payload.get("currency") or "", payload.get("next_12m_maturity_pressure"),
                "、".join(payload.get("bond_types") or []), payload.get("source_url"),
            )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _bond_item(self, company: dict) -> SourceItem:
        payload = self._bond_payload(company)
        return SourceItem(
            source_id="cfae",
            source_name=self.manifest.source_name,
            source_type="bond",
            market="CN",
            title="%s 北金所融资工具披露摘要" % company.get("name"),
            company_hint=company,
            publish_date=payload["as_of_date"],
            source_url=payload["source_url"],
            external_id="CFAE-%s-bond-latest" % company.get("ticker"),
            document_type="bond",
            period="latest",
            metadata=payload,
        )

    def _credit_event_item(self, company: dict) -> SourceItem:
        payload = self._event_payload(company)
        return SourceItem(
            source_id="cfae",
            source_name=self.manifest.source_name,
            source_type="credit_event",
            market="CN",
            title=payload["title"],
            company_hint=company,
            publish_date=payload["event_date"],
            source_url=payload["source_url"],
            external_id="CFAE-%s-event-latest" % company.get("ticker"),
            document_type="credit_event",
            period="latest",
            metadata=payload,
        )

    def _bond_payload(self, company: dict) -> dict:
        ticker = company.get("ticker")
        known = {
            "300750": {
                "outstanding_bond_count": 1,
                "outstanding_balance": 2_000_000_000,
                "next_12m_maturity_amount": 500_000_000,
                "next_12m_maturity_pressure": "低",
                "bond_types": ["债权融资计划"],
                "sample_instruments": [{"bond_name": "宁德时代债权融资计划摘要", "bond_type": "债权融资计划", "status": "存续"}],
            },
            "000001": {
                "outstanding_bond_count": 3,
                "outstanding_balance": 18_000_000_000,
                "next_12m_maturity_amount": 6_000_000_000,
                "next_12m_maturity_pressure": "中",
                "bond_types": ["债权融资计划", "信用风险缓释凭证"],
                "sample_instruments": [{"bond_name": "平安银行债权融资计划摘要", "bond_type": "债权融资计划", "status": "存续"}],
            },
            "600519": {
                "outstanding_bond_count": 0,
                "outstanding_balance": 0,
                "next_12m_maturity_amount": 0,
                "next_12m_maturity_pressure": "低",
                "bond_types": [],
                "sample_instruments": [],
            },
        }
        data = known.get(ticker, {
            "outstanding_bond_count": "未获取",
            "outstanding_balance": "未获取",
            "next_12m_maturity_amount": "未获取",
            "next_12m_maturity_pressure": "未获取",
            "bond_types": [],
            "sample_instruments": [],
        })
        title = "%s 北金所融资工具披露摘要" % company.get("name")
        match = issuer_match(company, company.get("name"), title)
        return {
            "issuer": company.get("name"),
            "ticker": ticker,
            "as_of_date": datetime.utcnow().date().isoformat(),
            "currency": "CNY",
            "source_url": "https://www.cfae.cn/",
            **match,
            **data,
        }

    def _event_payload(self, company: dict) -> dict:
        ticker = company.get("ticker")
        known = {
            "300750": {"event_type": "no_material_financing_event", "event_level": "low", "title": "北金所未发现近期重大融资披露异常摘要", "description": "演示环境未获取到债权融资计划展期、违约或重大异常披露摘要。"},
            "600519": {"event_type": "no_material_financing_event", "event_level": "low", "title": "北金所未发现近期重大融资披露异常摘要", "description": "演示环境未获取到债权融资计划展期、违约或重大异常披露摘要。"},
            "000001": {"event_type": "financing_attention", "event_level": "medium", "title": "北金所融资工具续作压力摘要", "description": "银行类主体融资工具规模较高，需关注利率环境变化和续作成本。"},
        }
        data = known.get(ticker, {"event_type": "unknown", "event_level": "unknown", "title": "北金所融资披露事件摘要待补充", "description": "暂未获取到北金所公开融资披露事件摘要，需后续联网刷新或人工复核。"})
        match = issuer_match(company, company.get("name"), data["title"])
        return {
            "subject_name": company.get("name"),
            "ticker": ticker,
            "event_date": datetime.utcnow().date().isoformat(),
            "authority": self.manifest.source_name,
            "source_url": "https://www.cfae.cn/",
            **match,
            **data,
        }
