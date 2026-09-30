"""Project, item-type, item-list, and evidence-list endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.core.deps import SessionDep
from app.repositories import evidence as evidence_repo
from app.repositories import projects as project_repo
from app.schemas.evidence import EvidenceRead
from app.schemas.item import ItemRead
from app.schemas.project import ItemTypeRead, ProjectNode, ProjectRead
from app.services import item_service, project_service

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
    counts = evidence_repo.evidence_link_counts(session, project_id)
    return [
        EvidenceRead(
            id=e.id,
            project_id=e.project_id,
            kind=e.kind,
            fqn=e.fqn,
            name=e.name,
            in_git=e.in_git,
            in_regression=e.in_regression,
            link_count=counts.get(e.id, 0),
        )
        for e in evidence_repo.list_evidence(session, project_id)
    ]
