from __future__ import annotations

from typing import List

from backend.data_sources.hk_index import HKIndex, normalize_hk_ticker
from backend.data_sources.hkex_client import HKEXClient


class HKShareSource:
    def __init__(self):
        self.index = HKIndex()
        self.hkex = HKEXClient()

    def search_companies(self, query: str) -> List[dict]:
        return self.index.search(query, limit=20)

    def resolve_company(self, ticker_or_name: str) -> dict:
        return self.index.resolve(ticker_or_name)

    def top_companies(self, limit: int = 80) -> List[dict]:
        return self.index.top(limit=limit)

    def coverage(self) -> dict:
        return self.index.coverage()

    def list_reports(self, company: dict) -> List[dict]:
        company = {**company, "ticker": normalize_hk_ticker(company["ticker"])}
        return self.hkex.list_reports(company)

    def fetch_financial_dataset(self, company: dict, periods=None, period_type: str = "annual") -> dict:
        company = {**company, "ticker": normalize_hk_ticker(company["ticker"])}
        return self.hkex.fetch_financial_dataset(company, periods=periods, period_type=period_type)
