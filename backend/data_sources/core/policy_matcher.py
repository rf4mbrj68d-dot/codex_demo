from __future__ import annotations

from backend.data_sources.core.issuer_matcher import issuer_match


INDUSTRY_POLICY_TERMS = {
    "新能源": ["新能源", "动力电池", "储能", "绿色低碳", "节能降碳", "新型能源体系"],
    "动力电池": ["动力电池", "储能", "新能源", "绿色低碳", "新型能源体系"],
    "电力设备": ["电力", "能源", "电网", "储能", "新型能源体系"],
    "白酒": ["扩大内需", "消费", "品牌消费", "现代服务业"],
    "金融": ["信用", "融资", "民间投资", "营商环境", "中小企业"],
    "家电": ["设备更新", "消费品以旧换新", "扩大内需", "绿色智能家电"],
    "互联网": ["数字经济", "平台经济", "数据要素", "人工智能"],
    "基建": ["基础设施", "交通", "水利", "城市更新", "重大项目"],
    "环保": ["节能降碳", "污染治理", "循环经济", "绿色低碳"],
    "制造": ["设备更新", "智能制造", "先进制造", "产业升级"],
}


def policy_match(company: dict, title: str, text: str = "", tags: list[str] | None = None, issuer_name: str | None = None) -> dict:
    direct = issuer_match(company, issuer_name or company.get("name"), "%s %s" % (title, text[:200]))
    if direct.get("match_confidence", 0) >= 0.9 and issuer_name:
        return {
            **direct,
            "relevance_level": "A",
            "matched_terms": [issuer_name],
        }

    haystack = "%s %s %s" % (title or "", text or "", " ".join(tags or []))
    industry = company.get("industry") or ""
    short_name = company.get("short_name") or company.get("name") or ""
    if short_name and short_name in haystack:
        return {
            "matched": True,
            "match_confidence": 0.9,
            "match_method": "company_name_in_policy",
            "relevance_level": "A",
            "matched_terms": [short_name],
        }

    terms = _terms_for_industry(industry)
    matched_terms = [term for term in terms if term and term in haystack]
    if len(matched_terms) >= 2:
        return {
            "matched": True,
            "match_confidence": 0.82,
            "match_method": "industry_policy_match",
            "relevance_level": "B",
            "matched_terms": matched_terms[:6],
        }
    if matched_terms:
        return {
            "matched": True,
            "match_confidence": 0.68,
            "match_method": "weak_industry_policy_match",
            "relevance_level": "C",
            "matched_terms": matched_terms,
        }
    return {
        "matched": False,
        "match_confidence": 0.4,
        "match_method": "policy_unrelated",
        "relevance_level": "D",
        "matched_terms": [],
    }


def _terms_for_industry(industry: str) -> list[str]:
    result = []
    for key, terms in INDUSTRY_POLICY_TERMS.items():
        if key in (industry or ""):
            result.extend(terms)
    if not result:
        result.extend(["扩大内需", "设备更新", "绿色低碳", "重大项目", "民间投资"])
    return list(dict.fromkeys(result))
