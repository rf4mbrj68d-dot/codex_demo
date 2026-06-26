from __future__ import annotations

import re
from typing import List


HK_TOP_COMPANIES = [
    {"ticker": "00700", "name": "腾讯控股", "short_name": "腾讯控股", "industry": "互联网"},
    {"ticker": "09988", "name": "阿里巴巴-W", "short_name": "阿里巴巴", "industry": "互联网零售"},
    {"ticker": "03690", "name": "美团-W", "short_name": "美团", "industry": "本地生活"},
    {"ticker": "00941", "name": "中国移动", "short_name": "中国移动", "industry": "通信"},
    {"ticker": "01299", "name": "友邦保险", "short_name": "友邦保险", "industry": "保险"},
    {"ticker": "00005", "name": "汇丰控股", "short_name": "汇丰控股", "industry": "金融"},
    {"ticker": "00001", "name": "长和", "short_name": "长和", "industry": "综合企业"},
    {"ticker": "02318", "name": "中国平安", "short_name": "中国平安", "industry": "金融"},
]


class HKIndex:
    def search(self, query: str, limit: int = 20) -> List[dict]:
        normalized = _normalize_query(query)
        if not normalized:
            return self.top(limit)
        items = [
            item for item in HK_TOP_COMPANIES
            if normalized in item["ticker"].lower()
            or normalized in item["name"].lower()
            or normalized in (item.get("short_name") or "").lower()
            or normalized == normalize_hk_ticker(item["ticker"]).lower()
        ]
        return [_company(item) for item in items[:limit]]

    def resolve(self, ticker_or_name: str) -> dict:
        normalized = _normalize_query(ticker_or_name)
        ticker = normalize_hk_ticker(ticker_or_name)
        for item in HK_TOP_COMPANIES:
            if item["ticker"] == ticker or normalized in item["name"].lower() or normalized in (item.get("short_name") or "").lower():
                return _company(item)
        raise ValueError("暂未在港股头部公司索引中找到：%s" % ticker_or_name)

    def top(self, limit: int = 80) -> List[dict]:
        return [_company(item) for item in HK_TOP_COMPANIES[:limit]]

    def coverage(self) -> dict:
        return {"count": len(HK_TOP_COMPANIES), "source": "本地头部港股索引", "using_fallback": False}


def normalize_hk_ticker(value: str) -> str:
    text = str(value or "").strip().upper().replace(".HK", "")
    digits = re.sub(r"\D", "", text)
    return digits.zfill(5) if digits else text


def _normalize_query(value: str) -> str:
    text = str(value or "").strip().lower()
    if text.upper().endswith(".HK"):
        return normalize_hk_ticker(text).lower()
    return text


def _company(item: dict) -> dict:
    ticker = normalize_hk_ticker(item["ticker"])
    return {
        "id": "HK-%s" % ticker,
        "ticker": ticker,
        "name": item["name"],
        "short_name": item.get("short_name") or item["name"],
        "market": "HK",
        "exchange": "HKEX",
        "industry": item.get("industry") or "待识别行业",
        "source": "HKEX",
    }
