from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SourceManifest:
    source_id: str
    source_name: str
    enabled: bool
    markets: list[str]
    source_types: list[str]
    capabilities: list[str]
    rate_limit: dict[str, Any] = field(default_factory=dict)
    ttl: dict[str, str] = field(default_factory=dict)
    priority: int = 50

    @classmethod
    def from_dict(cls, payload: dict) -> "SourceManifest":
        return cls(
            source_id=payload["source_id"],
            source_name=payload.get("source_name") or payload["source_id"],
            enabled=bool(payload.get("enabled", True)),
            markets=list(payload.get("markets") or ["ALL"]),
            source_types=list(payload.get("source_types") or []),
            capabilities=list(payload.get("capabilities") or []),
            rate_limit=dict(payload.get("rate_limit") or {}),
            ttl=dict(payload.get("ttl") or {}),
            priority=int(payload.get("priority", 50)),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourceSearchRequest:
    company: dict
    source_type: str
    market: str
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    document_type: Optional[str] = None
    period: Optional[str] = None
    query: str = ""
    limit: int = 20


@dataclass
class SourceItem:
    source_id: str
    source_name: str
    source_type: str
    market: str
    title: str
    company_hint: dict
    publish_date: Optional[str] = None
    source_url: Optional[str] = None
    external_id: Optional[str] = None
    document_type: Optional[str] = None
    period: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def item_id(self) -> str:
        basis = {
            "source_id": self.source_id,
            "external_id": self.external_id,
            "source_url": self.source_url,
            "title": self.title,
            "market": self.market,
            "period": self.period,
            "company": self.company_hint.get("id") or self.company_hint.get("ticker"),
        }
        encoded = json.dumps(basis, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return "src_%s" % hashlib.sha1(encoded).hexdigest()[:24]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["source_item_id"] = self.item_id()
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "SourceItem":
        data = dict(payload)
        data.pop("source_item_id", None)
        return cls(**data)


@dataclass
class SourcePayload:
    item: SourceItem
    content_type: str
    raw_bytes: Optional[bytes] = None
    raw_text: Optional[str] = None
    structured_data: Optional[dict] = None
    fetched_at: str = field(default_factory=utc_now)
    content_hash: str = ""
    asset_path: Optional[str] = None

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = self.compute_hash()

    def compute_hash(self) -> str:
        if self.raw_bytes is not None:
            return hashlib.sha256(self.raw_bytes).hexdigest()
        basis = self.raw_text if self.raw_text is not None else json.dumps(self.structured_data or {}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

    def to_record(self) -> dict:
        return {
            "item": self.item.to_dict(),
            "content_type": self.content_type,
            "raw_text": self.raw_text,
            "structured_data": self.structured_data,
            "fetched_at": self.fetched_at,
            "content_hash": self.content_hash,
            "asset_path": self.asset_path,
            "raw_size": len(self.raw_bytes or b""),
        }


@dataclass
class SourceHealth:
    source_id: str
    status: str
    message: str = ""
    checked_at: str = field(default_factory=utc_now)
    latency_ms: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
