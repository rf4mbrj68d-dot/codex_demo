from __future__ import annotations

from backend.data_sources.core.source_models import SourcePayload


class SupplementaryNormalizer:
    """Convert supplemental adapter payloads into knowledge-store facts."""

    def persist(self, knowledge, company: dict, payload: SourcePayload) -> dict:
        source_type = payload.item.source_type
        data = payload.structured_data or payload.item.metadata or {}
        confidence = data.get("match_confidence")
        if confidence is not None and float(confidence) < 0.75:
            return {"kind": source_type, "count": 0, "status": "raw_only_low_confidence", "match_confidence": confidence}
        if source_type == "quote":
            knowledge.upsert_market_quote(company["id"], payload.item.source_id, data)
            return {"kind": "quote", "count": 1}
        if source_type == "rating":
            knowledge.upsert_rating_fact(company["id"], payload.item.source_id, data)
            return {"kind": "rating", "count": 1}
        if source_type == "bond":
            knowledge.upsert_bond_fact(company["id"], payload.item.source_id, data)
            return {"kind": "bond", "count": 1}
        if source_type == "credit_event":
            knowledge.upsert_credit_risk_event(company["id"], payload.item.source_id, data)
            return {"kind": "credit_event", "count": 1}
        if source_type == "policy_project_event":
            if data.get("relevance_level") not in {"A", "B"}:
                return {"kind": "policy_project_event", "count": 0, "status": "raw_only_low_relevance", "relevance_level": data.get("relevance_level")}
            knowledge.upsert_policy_project_event(company["id"], payload.item.source_id, data)
            return {"kind": "policy_project_event", "count": 1}
        return {"kind": source_type, "count": 0}
