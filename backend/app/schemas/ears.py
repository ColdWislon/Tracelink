"""Schemas for the EARS quality checker endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class EarsCheckRequest(BaseModel):
    text: str


class FindingRead(BaseModel):
    code: str
    message: str
    severity: str
    start: int
    end: int
    term: str | None = None


class EarsCheckResponse(BaseModel):
    pattern: str | None
    ok: bool
    findings: list[FindingRead]
