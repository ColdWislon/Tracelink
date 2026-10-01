"""Project, item-type, item-list, and evidence-list endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, SessionDep
from app.repositories import projects as project_repo
from app.schemas.baseline import BaselineCreate, BaselineDetail, BaselineRead
from app.schemas.dashboard import DashboardRead
from app.schemas.evidence import EvidenceCreate, EvidenceRead, RegressionRunRead
from app.schemas.item import ItemRead
from app.schemas.project import ItemTypeRead, ProjectNode, ProjectRead
from app.services import (
    baseline_service,
    dashboard_service,
    evidence_service,
    item_service,
    project_service,
    regression_service,
)
from app.services.item_service import DomainError

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectNode])
def list_projects(session: SessionDep) -> list[ProjectNode]:
    return project_service.build_project_tree(session)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, session: SessionDep) -> ProjectRead:
    project = project_repo.get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return ProjectRead.model_validate(project)


@router.get("/{project_id}/item-types", response_model=list[ItemTypeRead])
def list_item_types(project_id: uuid.UUID, session: SessionDep) -> list[ItemTypeRead]:
    types = project_repo.list_item_types(session, project_id)
    return [ItemTypeRead.model_validate(t) for t in types]


@router.get("/{project_id}/items", response_model=list[ItemRead])
def list_items(project_id: uuid.UUID, session: SessionDep) -> list[ItemRead]:
    return item_service.list_item_reads(session, project_id)


@router.get("/{project_id}/evidence", response_model=list[EvidenceRead])
def list_evidence(project_id: uuid.UUID, session: SessionDep) -> list[EvidenceRead]:
    return evidence_service.list_catalog(session, project_id)


@router.post("/{project_id}/evidence", response_model=EvidenceRead, status_code=201)
def create_evidence(
    project_id: uuid.UUID, payload: EvidenceCreate, session: SessionDep
) -> EvidenceRead:
    try:
        return evidence_service.create_evidence(
            session, project_id, payload.kind, payload.fqn, payload.name
        )
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{project_id}/runs", response_model=list[RegressionRunRead])
def list_runs(project_id: uuid.UUID, session: SessionDep) -> list[RegressionRunRead]:
    return regression_service.list_runs(session, project_id)


@router.get("/{project_id}/dashboard", response_model=DashboardRead)
def dashboard(project_id: uuid.UUID, session: SessionDep) -> DashboardRead:
    return dashboard_service.compute(session, project_id)


@router.get("/{project_id}/baselines", response_model=list[BaselineRead])
def list_baselines(project_id: uuid.UUID, session: SessionDep) -> list[BaselineRead]:
    return baseline_service.list_baselines(session, project_id)


@router.post("/{project_id}/baselines", response_model=BaselineDetail, status_code=201)
def create_baseline(
    project_id: uuid.UUID, payload: BaselineCreate, session: SessionDep, user: CurrentUser
) -> BaselineDetail:
    try:
        return baseline_service.create_baseline(session, project_id, payload, author=user)
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
