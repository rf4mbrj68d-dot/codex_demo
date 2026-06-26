from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.api.deps import services


router = APIRouter(prefix="/api/data", tags=["data-platform"])


class RefreshRequest(BaseModel):
    ticker: str = Field(min_length=1)
    market: str = "US"
    resource_type: str = "financial_dataset"


class PrewarmRequest(BaseModel):
    market: str = "ALL"
    resources: List[str] = ["financial_dataset", "documents"]
    limit: int = Field(default=20, ge=1, le=100)


@router.get("/status")
def data_status(ticker: str, market: str = "US", svc=Depends(services)):
    try:
        company = svc.company_service.resolve(ticker, market)
        return svc.data_service.resource_status(company)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/sources")
def data_sources(svc=Depends(services)):
    try:
        return svc.data_service.source_status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/supplementary")
def supplementary_context(ticker: str, market: str = "US", force: bool = False, svc=Depends(services)):
    try:
        company = svc.company_service.resolve(ticker, market)
        return {"company": company, "context": svc.data_service.get_supplementary_context(company, force=force)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/disclosures")
def supplementary_disclosures(ticker: str, market: str = "US", force: bool = False, svc=Depends(services)):
    try:
        company = svc.company_service.resolve(ticker, market)
        return {"company": company, "items": svc.data_service.supplementary_disclosures(company, force=force)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/ratings")
def rating_context(ticker: str, market: str = "US", force: bool = False, svc=Depends(services)):
    try:
        company = svc.company_service.resolve(ticker, market)
        return {"company": company, "items": svc.data_service.rating_context(company, force=force)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/credit-events")
def credit_event_context(ticker: str, market: str = "US", force: bool = False, svc=Depends(services)):
    try:
        company = svc.company_service.resolve(ticker, market)
        return {"company": company, "items": svc.data_service.credit_event_context(company, force=force)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/policy-project-events")
def policy_project_context(ticker: str, market: str = "US", force: bool = False, svc=Depends(services)):
    try:
        company = svc.company_service.resolve(ticker, market)
        return {"company": company, "items": svc.data_service.policy_project_context(company, force=force)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/refresh")
def refresh_data(request: RefreshRequest, svc=Depends(services)):
    try:
        company = svc.company_service.resolve(request.ticker, request.market)
        return svc.data_service.request_refresh(request.resource_type, company, {"trigger": "manual"})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/jobs/{job_id}")
def get_refresh_job(job_id: str, svc=Depends(services)):
    job = svc.data_service.get_refresh_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="刷新任务不存在")
    return job


@router.post("/prewarm")
def prewarm_data(request: PrewarmRequest, svc=Depends(services)):
    try:
        jobs = svc.data_service.request_prewarm(request.market, request.resources, request.limit)
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/knowledge/documents")
def knowledge_documents(ticker: str, market: str = "US", source_type: str = "", svc=Depends(services)):
    try:
        company = svc.company_service.resolve(ticker, market)
        return {"company": company, "items": svc.data_service.knowledge_documents(company, source_type)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/knowledge/blocks")
def knowledge_blocks(ticker: str, market: str = "US", query: str = "", limit: int = 20, svc=Depends(services)):
    try:
        company = svc.company_service.resolve(ticker, market)
        return {"company": company, "items": svc.data_service.knowledge_blocks(company, query, max(1, min(limit, 100)))}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/knowledge/financial-facts")
def knowledge_financial_facts(ticker: str, market: str = "US", period: List[str] = [], svc=Depends(services)):
    try:
        company = svc.company_service.resolve(ticker, market)
        return {"company": company, "items": svc.data_service.knowledge_financial_facts(company, period or None)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
