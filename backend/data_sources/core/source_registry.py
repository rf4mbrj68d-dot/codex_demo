from __future__ import annotations

from typing import Iterable, Optional

from backend.data_sources.core.source_models import SourceHealth, SourceItem, SourcePayload, SourceSearchRequest


class SourceRegistry:
    def __init__(self, adapters: Optional[Iterable] = None):
        self.adapters = {}
        for adapter in adapters or []:
            self.register(adapter)

    def register(self, adapter) -> None:
        self.adapters[adapter.manifest.source_id] = adapter

    def list_sources(self) -> list[dict]:
        return [adapter.manifest.to_dict() for adapter in self._enabled_adapters()]

    def find(self, market: str, source_type: str, capability: str = "search") -> list:
        market = (market or "ALL").upper()
        result = []
        for adapter in self._enabled_adapters():
            manifest = adapter.manifest
            markets = {item.upper() for item in manifest.markets}
            if "ALL" not in markets and market not in markets:
                continue
            if source_type and source_type not in manifest.source_types:
                continue
            if capability and capability not in manifest.capabilities:
                continue
            result.append(adapter)
        return sorted(result, key=lambda item: item.manifest.priority, reverse=True)

    def healthcheck_all(self) -> list[dict]:
        checks = []
        for adapter in self._enabled_adapters():
            try:
                checks.append(adapter.healthcheck().to_dict())
            except Exception as exc:
                checks.append(SourceHealth(adapter.manifest.source_id, "failed", str(exc)[:300]).to_dict())
        return checks

    def search(self, request: SourceSearchRequest) -> list[SourceItem]:
        items: list[SourceItem] = []
        seen = set()
        for adapter in self.find(request.market, request.source_type, "search"):
            try:
                for item in adapter.search(request):
                    key = item.item_id()
                    if key in seen:
                        continue
                    items.append(item)
                    seen.add(key)
                    if len(items) >= request.limit:
                        return items
            except Exception:
                continue
        return items

    def fetch(self, item: SourceItem) -> SourcePayload:
        adapter = self.adapters.get(item.source_id)
        if not adapter:
            raise ValueError("未注册的数据源：%s" % item.source_id)
        return adapter.fetch(item)

    def search_companies(self, query: str, market: str = "ALL") -> list[dict]:
        results = []
        for adapter in self.find(market, "company", "search_companies"):
            if hasattr(adapter, "search_companies"):
                results.extend(adapter.search_companies(query))
        return _dedupe_companies(results)

    def resolve_company(self, query: str, market: str) -> dict:
        errors = []
        for adapter in self.find(market, "company", "resolve_company"):
            if not hasattr(adapter, "resolve_company"):
                continue
            try:
                return adapter.resolve_company(query)
            except Exception as exc:
                errors.append(str(exc))
        raise ValueError("未能解析公司：%s；%s" % (query, "；".join(errors[:2])))

    def top_companies(self, market: str = "ALL", limit: int = 80) -> list[dict]:
        results = []
        for adapter in self.find(market, "company", "top_companies"):
            if hasattr(adapter, "top_companies"):
                results.extend(adapter.top_companies(limit=limit))
        return _dedupe_companies(results)

    def list_documents(self, company: dict, source_type: str = "filing", limit: int = 20) -> list[dict]:
        request = SourceSearchRequest(company=company, source_type=source_type, market=company.get("market", "ALL"), limit=limit)
        return [_source_item_to_document(company, item) for item in self.search(request)]

    def fetch_financial_dataset(self, company: dict, periods=None, period_type: str = "annual") -> dict:
        for adapter in self.find(company.get("market", "ALL"), "financial_dataset", "fetch_financial_dataset"):
            if hasattr(adapter, "fetch_financial_dataset"):
                return adapter.fetch_financial_dataset(company, periods=periods, period_type=period_type)
        raise ValueError("未找到财务数据适配器：%s" % company.get("market"))

    def fetch_document_payload(self, document: dict) -> SourcePayload:
        source_id = _source_id_from_document(document)
        adapter = self.adapters.get(source_id)
        if not adapter:
            raise ValueError("未找到文档数据源适配器：%s" % source_id)
        item = SourceItem(
            source_id=source_id,
            source_name=adapter.manifest.source_name,
            source_type=document.get("report_type") or "filing",
            market=document.get("market") or "",
            title=document.get("title") or document.get("id") or "",
            company_hint={"id": document.get("company_id"), "ticker": document.get("ticker")},
            publish_date=document.get("publish_date"),
            source_url=document.get("source_url"),
            external_id=document.get("id"),
            document_type=document.get("report_type"),
            period=document.get("period"),
            metadata=dict(document),
        )
        return adapter.fetch(item)

    def _enabled_adapters(self):
        return [adapter for adapter in self.adapters.values() if adapter.manifest.enabled]


def build_default_source_registry(sec_client=None, ashare_source=None, hk_source=None, encyclopedia_client=None) -> SourceRegistry:
    from backend.data_sources.adapters.baidu_finance_adapter import BaiduFinanceAdapter
    from backend.data_sources.adapters.chinabond_adapter import ChinaBondAdapter
    from backend.data_sources.adapters.chinamoney_adapter import ChinaMoneyAdapter
    from backend.data_sources.adapters.cfae_adapter import CfaeBondAdapter
    from backend.data_sources.adapters.credit_rating_adapter import CcxiAdapter, CspengyuanAdapter, LhRatingsAdapter
    from backend.data_sources.adapters.creditchina_adapter import CreditChinaAdapter
    from backend.data_sources.adapters.cninfo_adapter import CninfoAdapter
    from backend.data_sources.adapters.dagong_adapter import DagongRatingAdapter
    from backend.data_sources.adapters.dfratings_adapter import DfratingsAdapter
    from backend.data_sources.adapters.encyclopedia_adapter import EncyclopediaAdapter
    from backend.data_sources.adapters.exchange_disclosure_adapter import BseAdapter, SseAdapter, SzseAdapter
    from backend.data_sources.adapters.hkex_adapter import HkexAdapter
    from backend.data_sources.adapters.investment_project_adapter import InvestmentProjectAdapter
    from backend.data_sources.adapters.nafmii_adapter import NafmiiAdapter
    from backend.data_sources.adapters.newcentury_adapter import NewCenturyRatingAdapter
    from backend.data_sources.adapters.ndrc_policy_adapter import NdrcPolicyAdapter
    from backend.data_sources.adapters.sec_adapter import SecAdapter
    from backend.data_sources.adapters.shclearing_adapter import ShClearingAdapter
    from backend.data_sources.ashare_source import AShareSource
    from backend.data_sources.hk_source import HKShareSource
    from backend.services.sec_client import SecClient
    from backend.company_profile.wikipedia_client import EncyclopediaClient

    sec_client = sec_client or SecClient()
    ashare_source = ashare_source or AShareSource()
    hk_source = hk_source or HKShareSource()
    encyclopedia_client = encyclopedia_client or EncyclopediaClient()
    return SourceRegistry([
        SecAdapter(sec_client),
        CninfoAdapter(ashare_source),
        SseAdapter(),
        SzseAdapter(),
        BseAdapter(),
        HkexAdapter(hk_source),
        EncyclopediaAdapter(encyclopedia_client),
        BaiduFinanceAdapter(),
        DfratingsAdapter(),
        CcxiAdapter(),
        LhRatingsAdapter(),
        CspengyuanAdapter(),
        DagongRatingAdapter(),
        NewCenturyRatingAdapter(),
        ChinaBondAdapter(),
        ShClearingAdapter(),
        ChinaMoneyAdapter(),
        NafmiiAdapter(),
        CfaeBondAdapter(),
        CreditChinaAdapter(),
        NdrcPolicyAdapter(),
        InvestmentProjectAdapter(),
    ])


def _dedupe_companies(items: list[dict]) -> list[dict]:
    result = []
    seen = set()
    for item in items:
        key = (item.get("market"), item.get("ticker"))
        if key in seen:
            continue
        result.append(item)
        seen.add(key)
    return result


def _source_item_to_document(company: dict, item: SourceItem) -> dict:
    document_type = item.document_type or item.source_type
    period = item.period or item.metadata.get("period") or "reference"
    return {
        "id": item.external_id or "%s-%s-%s" % (company["id"], item.source_id.upper(), period),
        "company_id": company["id"],
        "report_type": document_type,
        "period": period,
        "publish_date": item.publish_date,
        "source_url": item.source_url,
        "title": item.title,
        "source_platform": item.source_name,
        "source_id": item.source_id,
        "market": item.market or company.get("market"),
        "form": item.metadata.get("form"),
        "parse_status": item.metadata.get("parse_status") or "source_adapter",
        **{key: value for key, value in item.metadata.items() if key not in {"id", "company_id"}},
    }


def _source_id_from_document(document: dict) -> str:
    if document.get("source_id"):
        return document["source_id"]
    platform = (document.get("source_platform") or "").lower()
    if "sec" in platform:
        return "sec"
    if "cninfo" in platform or "巨潮" in platform:
        return "cninfo"
    if "hkex" in platform or "港交" in platform:
        return "hkex"
    if document.get("report_type") in {"wikipedia", "baidubaike", "encyclopedia"}:
        return "encyclopedia"
    market = document.get("market")
    if market == "CN":
        return "cninfo"
    if market == "HK":
        return "hkex"
    return "sec"
