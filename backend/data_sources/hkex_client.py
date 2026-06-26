from __future__ import annotations

import re
from io import BytesIO
from typing import Dict, List, Optional

import requests

from backend.data_sources.hk_index import normalize_hk_ticker


HKEX_HEADERS = {
    "User-Agent": "FinancialReportMining/0.4",
    "Accept": "application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

HK_REPORT_FIXTURES: Dict[str, dict] = {
    "00700": {
        "company_name": "腾讯控股",
        "currency": "CNY",
        "reports": [
            {
                "period": "2024-FY",
                "publish_date": "2025-04-09",
                "source_url": "https://static.www.tencent.com/uploads/2025/04/09/2024-annual-report.pdf",
                "metrics": {
                    "revenue": 660257000000,
                    "net_profit": 194073000000,
                    "operating_cashflow": 280000000000,
                    "assets": 1821969000000,
                    "liabilities": 781437000000,
                    "equity": 1040532000000,
                    "inventory": 1194000000,
                    "receivables": 68983000000,
                },
            },
            {
                "period": "2023-FY",
                "publish_date": "2024-04-08",
                "source_url": "https://static.www.tencent.com/uploads/2024/04/08/2023-annual-report.pdf",
                "metrics": {
                    "revenue": 609015000000,
                    "net_profit": 157688000000,
                    "operating_cashflow": 222025000000,
                    "assets": 1577217000000,
                    "liabilities": 702915000000,
                    "equity": 874302000000,
                    "inventory": 1063000000,
                    "receivables": 57157000000,
                },
            },
            {
                "period": "2022-FY",
                "publish_date": "2023-04-06",
                "source_url": "https://static.www.tencent.com/uploads/2023/04/06/2022-annual-report.pdf",
                "metrics": {
                    "revenue": 554552000000,
                    "net_profit": 115649000000,
                    "operating_cashflow": 193269000000,
                    "assets": 1516533000000,
                    "liabilities": 706806000000,
                    "equity": 809727000000,
                    "inventory": 1082000000,
                    "receivables": 54495000000,
                },
            },
        ],
    },
    "09988": {
        "company_name": "阿里巴巴-W",
        "currency": "CNY",
        "reports": [
            {
                "period": "2024-FY",
                "publish_date": "2024-07-23",
                "source_url": "https://www.alibabagroup.com/document-1744138810327441408",
                "metrics": {
                    "revenue": 941168000000,
                    "net_profit": 79741000000,
                    "operating_cashflow": 182593000000,
                    "assets": 1777268000000,
                    "liabilities": 655154000000,
                    "equity": 1122114000000,
                    "inventory": 28530000000,
                    "receivables": 70419000000,
                },
            },
            {
                "period": "2023-FY",
                "publish_date": "2023-07-21",
                "source_url": "https://www.alibabagroup.com/document-1669706299189104640",
                "metrics": {
                    "revenue": 868687000000,
                    "net_profit": 65573000000,
                    "operating_cashflow": 199752000000,
                    "assets": 1753587000000,
                    "liabilities": 630971000000,
                    "equity": 1122616000000,
                    "inventory": 27786000000,
                    "receivables": 60381000000,
                },
            },
        ],
    },
    "03690": {
        "company_name": "美团-W",
        "currency": "CNY",
        "reports": [
            {
                "period": "2024-FY",
                "publish_date": "2025-04-15",
                "source_url": "https://about.meituan.com/investor-relations/annual-reports",
                "metrics": {
                    "revenue": 337592000000,
                    "net_profit": 35805000000,
                    "operating_cashflow": 66057000000,
                    "assets": 332337000000,
                    "liabilities": 156921000000,
                    "equity": 175416000000,
                    "inventory": 1200000000,
                    "receivables": 13271000000,
                },
            }
        ],
    },
}


class HKEXError(RuntimeError):
    pass


class HKEXClient:
    def __init__(self):
        self._http = requests.Session()
        self._http.trust_env = False

    def list_reports(self, company: dict) -> List[dict]:
        ticker = normalize_hk_ticker(company["ticker"])
        fixture = HK_REPORT_FIXTURES.get(ticker)
        if not fixture:
            raise HKEXError("港股 %s 暂未配置可解析的年报索引。" % ticker)
        reports = []
        for item in fixture["reports"]:
            reports.append({
                "id": "HK-%s-%s" % (ticker, item["period"]),
                "company_id": company["id"],
                "report_type": "annual",
                "period": item["period"],
                "publish_date": item.get("publish_date"),
                "source_url": item.get("source_url"),
                "parse_status": "hk_seeded_pdf",
                "title": "%s %s 年报" % (company["name"], item["period"]),
                "source_platform": "HKEX",
                "market": "HK",
            })
        return reports

    def fetch_financial_dataset(self, company: dict, periods: Optional[List[str]] = None, period_type: str = "annual") -> dict:
        ticker = normalize_hk_ticker(company["ticker"])
        fixture = HK_REPORT_FIXTURES.get(ticker)
        if not fixture:
            raise HKEXError("港股 %s 暂未配置可解析的财务数据集。" % ticker)
        requested = set(periods or [])
        records, filings = {}, {}
        for item in fixture["reports"]:
            if requested and item["period"] not in requested:
                continue
            record = self._record(company, item, fixture.get("currency") or "HKD")
            records[record["period"]] = record
            filings[record["sources"][0]] = {
                "form": record["form"],
                "report_date": record["end"],
                "filing_date": record["filed"],
                "url": item.get("source_url"),
            }
        if not records:
            raise HKEXError("未找到匹配的港股报告期。")
        return {"records": records, "filings": filings}

    def download_pdf(self, url: str) -> bytes:
        if not url or "annual-reports" in url or "document-" in url:
            raise HKEXError("该港股报告暂未提供可直接下载的 PDF URL。")
        response = self._http.get(url, headers=HKEX_HEADERS, timeout=30)
        response.raise_for_status()
        return response.content

    def extract_pdf_text_from_bytes(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(BytesIO(content))
            pages = [(page.extract_text() or "") for page in reader.pages[:160]]
            text = "\n\n".join("--- PAGE %s ---\n%s" % (index, page) for index, page in enumerate(pages, start=1))
        except Exception as exc:
            raise HKEXError("港股 PDF 文本抽取失败：%s" % exc) from exc
        if len(text.strip()) < 200:
            raise HKEXError("港股 PDF 文本过少，可能是扫描件或不可解析格式。")
        return text

    def fallback_report_text(self, company: dict, report: dict) -> str:
        ticker = normalize_hk_ticker(company["ticker"])
        fixture = HK_REPORT_FIXTURES.get(ticker) or {}
        matched = next((item for item in fixture.get("reports", []) if item["period"] == report["period"]), None)
        if not matched:
            return ""
        metrics = matched["metrics"]
        lines = [
            "%s %s 年度报告摘要" % (company["name"], matched["period"]),
            "公司主要通过互联网服务、金融科技及企业服务、网络广告、数字内容等业务取得收入。",
            "本报告期收入为 %s，净利润为 %s，经营现金流为 %s。" % (
                metrics.get("revenue"), metrics.get("net_profit"), metrics.get("operating_cashflow")
            ),
            "总资产为 %s，总负债为 %s，权益总额为 %s。" % (
                metrics.get("assets"), metrics.get("liabilities"), metrics.get("equity")
            ),
            "该文本为港股适配器保存的标准化摘要，用于演示统一知识整理层的文档块入库；真实部署可替换为 HKEX PDF 全文抽取。",
        ]
        return "\n\n".join(lines)

    def _record(self, company: dict, item: dict, currency: str) -> dict:
        period = item["period"]
        metrics = {
            key: {"value": value, "unit": currency, "label": _metric_label(key), "source_accn": "HK-%s-%s" % (company["ticker"], period)}
            for key, value in item["metrics"].items()
        }
        return {
            "period": period,
            "fy": int(period.split("-")[0]),
            "fp": period.split("-")[1],
            "form": "年度报告",
            "filed": item.get("publish_date"),
            "end": "%s-12-31" % period.split("-")[0],
            "metrics": metrics,
            "sources": ["HK-%s-%s" % (company["ticker"], period)],
        }


def _metric_label(key: str) -> str:
    return {
        "revenue": "营业收入",
        "net_profit": "净利润",
        "operating_cashflow": "经营现金流",
        "assets": "总资产",
        "liabilities": "总负债",
        "equity": "股东权益",
        "inventory": "存货",
        "receivables": "应收账款",
    }.get(key, key)
