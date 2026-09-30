"""EARS quality-check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.ears import EarsCheckRequest, EarsCheckResponse, FindingRead
from app.services.domain.ears import check_ears

router = APIRouter(prefix="/ears", tags=["ears"])


@router.post("/check", response_model=EarsCheckResponse)
def check(payload: EarsCheckRequest) -> EarsCheckResponse:
    report = check_ears(payload.text)
    return EarsCheckResponse(
        pattern=report.pattern,
        ok=report.ok,
        findings=[
            FindingRead(
                code=f.code,
                message=f.message,
                severity=f.severity,
                start=f.start,
                end=f.end,
                term=f.term,
            )
            for f in report.findings
        ],
    )
