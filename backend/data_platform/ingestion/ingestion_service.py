from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Optional

from backend.data_platform.normalizers import SupplementaryNormalizer
from backend.data_platform.repository import utc_now
from backend.data_sources.core.source_models import SourceItem, SourcePayload, SourceSearchRequest


class IngestionService:
    """Bridge source adapters and the unified knowledge store."""

    def __init__(self, registry, repository, knowledge, storage_dir: Path):
        self.registry = registry
        self.repository = repository
        self.knowledge = knowledge
        self.storage_dir = storage_dir
        self.assets_dir = storage_dir / "assets" / "source_payloads"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.supplementary_normalizer = SupplementaryNormalizer()

    def search_source_items(self, company: dict, source_type: str, limit: int = 20, **filters) -> list[SourceItem]:
        request = SourceSearchRequest(
            company=company,
            source_type=source_type,
            market=company.get("market", "ALL"),
            date_from=filters.get("date_from"),
            date_to=filters.get("date_to"),
            document_type=filters.get("document_type"),
            period=filters.get("period"),
            query=filters.get("query", ""),
            limit=limit,
        )
        items = self.registry.search(request)
        for item in items:
            self.repository.upsert_source_item(item.to_dict(), company_id=company["id"])
        return items

    def ingest_documents(self, company: dict, source_type: str = "filing", limit: int = 20, **filters) -> list[dict]:
        items = self.search_source_items(company, source_type, limit=limit, **filters)
        return [self._source_item_to_document(company, item) for item in items]

    def fetch_payload(self, item: SourceItem, company: Optional[dict] = None, ttl: Optional[timedelta] = None, force: bool = False) -> SourcePayload:
        cached = None if force else self.repository.get_source_payload(item.item_id(), allow_stale=ttl is None)
        if cached and cached.get("raw_text") is not None:
            return SourcePayload(
                item=item,
                content_type=cached["content_type"],
                raw_text=cached.get("raw_text"),
                structured_data=cached.get("structured_data"),
                fetched_at=cached.get("fetched_at") or utc_now(),
                content_hash=cached.get("content_hash") or "",
                asset_path=cached.get("asset_path"),
            )
        payload = self.registry.fetch(item)
        if payload.raw_bytes:
            payload.asset_path = str(self._write_source_asset(item, payload.raw_bytes).relative_to(self.storage_dir))
        self.repository.upsert_source_item(item.to_dict(), company_id=(company or item.company_hint).get("id"))
        self.repository.upsert_source_payload(item.item_id(), payload.to_record(), expires_at=None)
        return payload

    def fetch_document_payload(self, document: dict, company: Optional[dict] = None, force: bool = False) -> SourcePayload:
        payload = self.registry.fetch_document_payload(document)
        item = payload.item
        if payload.raw_bytes:
            payload.asset_path = str(self._write_source_asset(item, payload.raw_bytes).relative_to(self.storage_dir))
        self.repository.upsert_source_item(item.to_dict(), company_id=document.get("company_id") or (company or {}).get("id"))
        self.repository.upsert_source_payload(item.item_id(), payload.to_record(), expires_at=None)
        return payload

    def ingest_supplementary(self, company: dict, source_types: Optional[list[str]] = None, force: bool = False) -> dict:
        source_types = source_types or ["quote", "rating", "bond", "credit_event", "policy_project_event"]
        result = {}
        for source_type in source_types:
            persisted = []
            for item in self.search_source_items(company, source_type, limit=8):
                payload = self.fetch_payload(item, company=company, force=force)
                persisted.append(self.supplementary_normalizer.persist(self.knowledge, company, payload))
            result[source_type] = persisted
        return result

    def supplementary_context(self, company: dict, force: bool = False) -> dict:
        if force:
            self.ingest_supplementary(company, force=True)
        quote = self.knowledge.latest_market_quote(company["id"])
        ratings = self.knowledge.list_rating_facts(company["id"], limit=6)
        bonds = self.knowledge.list_bond_facts(company["id"], limit=6)
        credit_events = self.knowledge.list_credit_risk_events(company["id"], limit=10)
        policy_project_events = self.knowledge.list_policy_project_events(company["id"], limit=6)
        missing_types = []
        if not quote:
            missing_types.append("quote")
        if not ratings:
            missing_types.append("rating")
        if not bonds:
            missing_types.append("bond")
        if not credit_events:
            missing_types.append("credit_event")
        if company.get("market") == "CN" and not policy_project_events:
            missing_types.append("policy_project_event")
        if missing_types:
            self.ingest_supplementary(company, source_types=missing_types)
            quote = self.knowledge.latest_market_quote(company["id"])
            ratings = self.knowledge.list_rating_facts(company["id"], limit=6)
            bonds = self.knowledge.list_bond_facts(company["id"], limit=6)
            credit_events = self.knowledge.list_credit_risk_events(company["id"], limit=10)
            policy_project_events = self.knowledge.list_policy_project_events(company["id"], limit=6)
        return {"quote": quote, "ratings": ratings, "bonds": bonds, "credit_events": credit_events, "policy_project_events": policy_project_events}

    def _source_item_to_document(self, company: dict, item: SourceItem) -> dict:
        document_type = item.document_type or item.source_type
        period = item.period or item.metadata.get("period") or "reference"
        document = {
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
        }
        document.update({key: value for key, value in item.metadata.items() if key not in document})
        return document

    def _write_source_asset(self, item: SourceItem, content: bytes) -> Path:
        suffix = {
            "application/pdf": ".pdf",
            "text/html": ".html",
            "text/plain": ".txt",
            "application/json": ".json",
        }.get(item.metadata.get("content_type"), "")
        path = self.assets_dir / ("%s%s" % (item.item_id(), suffix or ".bin"))
        path.write_bytes(content)
        return path
