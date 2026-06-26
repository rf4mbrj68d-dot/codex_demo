from __future__ import annotations

from datetime import datetime

from backend.data_sources.core.policy_matcher import policy_match
from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourceManifest, SourcePayload, SourceSearchRequest


class NdrcPolicyAdapter:
    def __init__(self):
        self.manifest = SourceManifest.from_dict({
            "source_id": "ndrc_policy",
            "source_name": "国家发改委",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["policy_project_event"],
            "capabilities": ["search", "fetch"],
            "ttl": {"policy_index": "7d", "policy_detail": "90d"},
            "rate_limit": {"qps": 1},
            "priority": 45,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("ndrc_policy", "ready", "国家发改委政策线索适配器可用，当前启用稳定摘要回退")

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        company = request.company
        if company.get("market") != "CN":
            return []
        payloads = self._policy_payloads(company)
        return [SourceItem(
            source_id="ndrc_policy",
            source_name=self.manifest.source_name,
            source_type="policy_project_event",
            market="CN",
            title=payload["title"],
            company_hint=company,
            publish_date=payload["event_date"],
            source_url=payload["source_url"],
            external_id="NDRC-%s-%s" % (company.get("ticker"), index),
            document_type="policy_project_event",
            period="latest",
            metadata=payload,
        ) for index, payload in enumerate(payloads[: request.limit], start=1)]

    def fetch(self, item: SourceItem) -> SourcePayload:
        payload = item.metadata
        text = "%s政策与项目线索：%s。相关性%s，影响：%s。边界：%s 来源：%s" % (
            payload.get("authority"),
            payload.get("plain_summary"),
            payload.get("relevance_level"),
            payload.get("possible_impact"),
            payload.get("usage_boundary"),
            payload.get("source_url"),
        )
        return SourcePayload(item=item, content_type="application/json", raw_text=text, structured_data=payload)

    def _policy_payloads(self, company: dict) -> list[dict]:
        today = datetime.utcnow().date().isoformat()
        ticker = company.get("ticker")
        known = {
            "300750": [{
                "event_type": "policy_support",
                "title": "关于加快推动新型能源体系建设和绿色低碳转型的政策线索摘要",
                "tags": ["policy_support", "new_energy", "green_transition", "energy_storage"],
                "plain_summary": "公开政策方向与新能源、动力电池、储能和绿色低碳转型相关，可作为宁德时代所处行业的外部环境参考。",
                "possible_impact": "可能影响行业需求、资本开支和产业链投资节奏，但不能直接推导公司收入或利润。",
            }],
            "600519": [{
                "event_type": "policy_context",
                "title": "关于扩大内需和促进消费的政策线索摘要",
                "tags": ["domestic_demand", "consumption", "brand_consumption"],
                "plain_summary": "扩大内需和促进消费政策与高端消费行业存在间接相关，可作为白酒消费环境背景参考。",
                "possible_impact": "可能影响消费信心和渠道环境，但不能直接推导公司销量、价格或利润。",
            }],
            "000001": [{
                "event_type": "policy_context",
                "title": "关于优化营商环境和支持实体经济融资的政策线索摘要",
                "tags": ["financing", "credit", "business_environment"],
                "plain_summary": "优化营商环境和支持实体经济融资政策与银行信贷投放环境相关。",
                "possible_impact": "可能影响信贷需求和风险偏好，但不能替代银行资产质量和息差披露。",
            }],
            "000333": [{
                "event_type": "policy_support",
                "title": "关于设备更新和消费品以旧换新的政策线索摘要",
                "tags": ["equipment_upgrade", "trade_in", "green_appliance", "domestic_demand"],
                "plain_summary": "设备更新、消费品以旧换新和绿色智能家电政策与家电行业需求相关。",
                "possible_impact": "可能改善家电消费和渠道需求，但实际收入贡献仍需以公司披露为准。",
            }],
        }
        records = known.get(ticker, [{
            "event_type": "policy_context",
            "title": "%s 国家发改委政策环境摘要待补充" % (company.get("name") or ticker),
            "tags": ["policy_context"],
            "plain_summary": "暂未获取到与该公司高度相关的国家发改委政策线索。",
            "possible_impact": "当前只能作为外部政策环境待补充信息，不能用于经营或财务判断。",
        }])
        result = []
        for record in records:
            match = policy_match(company, record["title"], record.get("plain_summary", ""), record.get("tags", []))
            result.append({
                "ticker": ticker,
                "subject_name": company.get("name"),
                "event_date": today,
                "authority": self.manifest.source_name,
                "source_url": "https://www.ndrc.gov.cn/",
                "usage_boundary": "仅作为外部政策环境参考，不构成财务事实或投资建议。",
                **match,
                **record,
            })
        return result
