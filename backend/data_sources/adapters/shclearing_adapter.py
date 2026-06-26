from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class ShClearingAdapter:
    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "shclearing",
            "source_name": "上海清算所",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["bond", "credit_event"],
            "capabilities": ["search", "fetch"],
            "ttl": {"bond_index": "7d", "credit_event_index": "7d"},
            "rate_limit": {"qps": 1},
            "priority": 70,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("shclearing", "ready", "上海清算所债务融资工具适配器可用，当前启用稳定摘要回退")

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
            text = "%s清算所事件：%s，级别%s。%s" % (
                payload.get("subject_name"), payload.get("title"), payload.get("event_level"), payload.get("description")
            )
        else:
            text = "%s清算所债务融资工具补充：存续工具%s只，存续规模%s%s，未来12个月到期压力%s。" % (
                payload.get("issuer"), payload.get("outstanding_bond_count"), payload.get("outstanding_balance"),
                payload.get("currency") or "", payload.get("next_12m_maturity_pressure")
            )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _bond_item(self, company: dict) -> SourceItem:
        payload = self._bond_payload(company)
        return SourceItem(
            source_id="shclearing",
            source_name=self.manifest.source_name,
            source_type="bond",
            market="CN",
            title="%s 上海清算所债务融资工具摘要" % company.get("name"),
            company_hint=company,
            publish_date=payload["as_of_date"],
            source_url="https://www.shclearing.com/",
            external_id="SHCLEARING-%s-bond-latest" % company.get("ticker"),
            document_type="bond",
            period="latest",
            metadata=payload,
        )

    def _credit_event_item(self, company: dict) -> SourceItem:
        payload = self._event_payload(company)
        return SourceItem(
            source_id="shclearing",
            source_name=self.manifest.source_name,
            source_type="credit_event",
            market="CN",
            title=payload["title"],
            company_hint=company,
            publish_date=payload["event_date"],
            source_url=payload["source_url"],
            external_id="SHCLEARING-%s-event-latest" % company.get("ticker"),
            document_type="credit_event",
            period="latest",
            metadata=payload,
        )

    def _bond_payload(self, company: dict) -> dict:
        known = {
            "300750": {
                "outstanding_bond_count": 2,
                "outstanding_balance": 5_000_000_000,
                "next_12m_maturity_amount": 1_000_000_000,
                "next_12m_maturity_pressure": "低",
                "bond_types": ["超短期融资券", "中期票据"],
                "events": ["关注滚续发行成本"],
            },
            "000001": {
                "outstanding_bond_count": 6,
                "outstanding_balance": 42_000_000_000,
                "next_12m_maturity_amount": 12_000_000_000,
                "next_12m_maturity_pressure": "中",
                "bond_types": ["同业存单", "金融债"],
                "events": ["关注货币市场利率和流动性环境"],
            },
            "600519": {
                "outstanding_bond_count": 0,
                "outstanding_balance": 0,
                "next_12m_maturity_amount": 0,
                "next_12m_maturity_pressure": "低",
                "bond_types": [],
                "events": [],
            },
        }
        data = known.get(company.get("ticker"), {
            "outstanding_bond_count": "未获取",
            "outstanding_balance": "未获取",
            "next_12m_maturity_amount": "未获取",
            "next_12m_maturity_pressure": "未获取",
            "bond_types": [],
            "events": ["暂未获取到上海清算所债务融资工具摘要"],
        })
        return {
            "issuer": company.get("name"),
            "ticker": company.get("ticker"),
            "as_of_date": datetime.utcnow().date().isoformat(),
            "currency": "CNY",
            "source_url": "https://www.shclearing.com/",
            **data,
        }

    def _event_payload(self, company: dict) -> dict:
        ticker = company.get("ticker")
        event_map = {
            "000001": {
                "event_type": "bondholder_meeting",
                "event_level": "medium",
                "title": "债务融资工具持有人会议公告摘要",
                "description": "出现债务融资工具持有人会议类摘要，需关注后续兑付安排与融资成本变化。",
            },
            "300750": {
                "event_type": "normal_repayment_notice",
                "event_level": "low",
                "title": "未发现清算所重大异常兑付事件摘要",
                "description": "演示环境未获取到展期、违约或未按期兑付类高等级风险摘要。",
            },
            "600519": {
                "event_type": "no_material_event",
                "event_level": "low",
                "title": "未发现清算所重大债务融资风险摘要",
                "description": "演示环境未获取到清算所债务融资工具重大异常公告摘要。",
            },
        }
        data = event_map.get(ticker, {
            "event_type": "unknown",
            "event_level": "unknown",
            "title": "清算所信用事件摘要待补充",
            "description": "暂未获取到上海清算所公开事件摘要，需后续联网刷新或人工复核。",
        })
        return {
            "subject_name": company.get("name"),
            "ticker": ticker,
            "event_date": datetime.utcnow().date().isoformat(),
            "authority": "上海清算所",
            "source_url": "https://www.shclearing.com/",
            **data,
        }
