from __future__ import annotations

import re
from difflib import SequenceMatcher


COMPANY_SUFFIXES = (
    "股份有限公司",
    "有限责任公司",
    "集团股份有限公司",
    "集团有限公司",
    "控股有限公司",
    "股份公司",
    "有限公司",
    "集团",
    "公司",
)


def normalize_issuer_name(value: str | None) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[\s（）()【】\\[\\]·,，.。:：;；\\-_/]+", "", text)
    for suffix in COMPANY_SUFFIXES:
        text = text.replace(suffix.lower(), "")
    return text


def issuer_match(company: dict, issuer_name: str | None, title: str | None = None) -> dict:
    """Return a conservative local match score for supplemental CN sources."""

    company_name = company.get("name") or company.get("company_name") or ""
    ticker = company.get("ticker") or ""
    aliases = [
        company_name,
        company.get("short_name") or "",
        company.get("name_cn") or "",
        company.get("name_en") or "",
    ]
    issuer_norm = normalize_issuer_name(issuer_name)
    title_norm = normalize_issuer_name(title)
    alias_norms = [normalize_issuer_name(item) for item in aliases if item]
    alias_norms = [item for item in alias_norms if item]

    if issuer_norm and issuer_norm in alias_norms:
        return {"matched": True, "match_confidence": 0.98, "match_method": "normalized_full_name"}
    if issuer_norm:
        for alias in alias_norms:
            if alias and (alias in issuer_norm or issuer_norm in alias):
                return {"matched": True, "match_confidence": 0.92, "match_method": "normalized_contains"}
        best = max((SequenceMatcher(None, issuer_norm, alias).ratio() for alias in alias_norms), default=0)
        if best >= 0.82:
            return {"matched": True, "match_confidence": round(best, 2), "match_method": "fuzzy_name"}

    if ticker and ticker in (title or ""):
        return {"matched": True, "match_confidence": 0.86, "match_method": "ticker_in_title"}
    if title_norm:
        for alias in alias_norms:
            if alias and alias in title_norm:
                return {"matched": True, "match_confidence": 0.8, "match_method": "alias_in_title"}

    return {"matched": False, "match_confidence": 0.5, "match_method": "fallback_unverified"}
