from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.policy_matcher import policy_match
from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class InvestmentProjectAdapter:
    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "investment_project",
            "source_name": "投资项目在线审批监管平台",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["policy_project_event"],
            "capabilities": ["search", "fetch"],
            "ttl": {"project_index": "7d", "project_detail": "30d"},
            "rate_limit": {"qps": 1},
            "priority": 46,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("investment_project", "ready", "投资项目在线审批监管平台适配器可用，当前启用稳定摘要回退")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        if company.get("market") != "CN":
            return []
        payloads = self._project_payloads(company)
        return [SourceItem(
            source_id="investment_project",
            source_name=self.manifest.source_name,
            source_type="policy_project_event",
            market="CN",
            title=payload["title"],
            company_hint=company,
            publish_date=payload["event_date"],
            source_url=payload["source_url"],
            external_id="INVPROJECT-%s-%s" % (company.get("ticker"), index),
            document_type="policy_project_event",
            period="latest",
            metadata=payload,
        ) for index, payload in enumerate(payloads[: request.limit], start=1)]

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata
        text = "%s项目线索：%s。相关性%s，可能影响：%s。边界：%s 来源：%s" % (
            payload.get("authority"),
            payload.get("plain_summary"),
            payload.get("relevance_level"),
            payload.get("possible_impact"),
            payload.get("usage_boundary"),
            payload.get("source_url"),
        )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _project_payloads(self, company: dict) -> list[dict]:
        today = datetime.utcnow().date().isoformat()
        ticker = company.get("ticker")
        known = {
            "300750": [{
                "event_type": "project_recommendation",
                "event_level": "info",
                "title": "宁德时代相关新能源和储能产业链项目推介线索摘要",
                "tags": ["project_recommendation", "new_energy", "energy_storage", "private_investment"],
                "plain_summary": "投资项目平台的重大项目、民间资本推介和新型能源相关栏目可作为动力电池及储能产业链项目机会背景。",
                "possible_impact": "可能提示行业项目储备和资本开支方向，但未直接证明公司获得订单或项目收益。",
                "project_status": "线索待核验",
            }],
            "000333": [{
                "event_type": "project_recommendation",
                "event_level": "info",
                "title": "美的集团相关绿色智能家电和设备更新项目线索摘要",
                "tags": ["project_recommendation", "equipment_upgrade", "green_appliance", "trade_in"],
                "plain_summary": "投资项目平台的设备更新、消费品以旧换新相关项目可作为家电行业需求背景。",
                "possible_impact": "可能影响家电更新需求和渠道动销，但不能直接推导公司收入。",
                "project_status": "线索待核验",
            }],
            "600519": [{
                "event_type": "project_context",
                "event_level": "info",
                "title": "贵州茅台相关消费和文旅项目环境线索摘要",
                "tags": ["project_context", "consumption", "culture_tourism"],
                "plain_summary": "投资项目平台消费、文旅和区域重大项目可能影响消费环境，但与公司经营关联偏间接。",
                "possible_impact": "仅能作为外部环境背景，不能用于推断销量或价格。",
                "project_status": "间接相关",
            }],
        }
        records = known.get(ticker, [{
            "event_type": "project_context",
            "event_level": "unknown",
            "title": "%s 投资项目平台线索待补充" % (company.get("name") or ticker),
            "tags": ["project_context"],
            "plain_summary": "暂未获取到与该公司高相关的公开项目审批或推介线索。",
            "possible_impact": "当前只能作为项目线索待补充信息，不能用于经营或财务判断。",
            "project_status": "未获取",
        }])
        result = []
        for record in records:
            match = policy_match(company, record["title"], record.get("plain_summary", ""), record.get("tags", []))
            result.append({
                "ticker": ticker,
                "subject_name": company.get("name"),
                "event_date": today,
                "authority": self.manifest.source_name,
                "source_url": "https://new.tzxm.gov.cn/",
                "usage_boundary": "仅作为项目审批、推介或投资环境线索，不构成财务事实或投资建议。",
                **match,
                **record,
            })
        return result
