"""Project read orchestration: build the hierarchy tree with item counts."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import Project
from app.repositories import projects as project_repo
from app.schemas.project import ProjectNode, VariantRead


def _node(project: Project, counts: dict[uuid.UUID, int]) -> ProjectNode:
    return ProjectNode(
        id=project.id,
        key=project.key,
        name=project.name,
        kind=project.kind,
        parent_id=project.parent_id,
        is_ip_library=project.is_ip_library,
        description=project.description,
        variants=[VariantRead.model_validate(v) for v in project.variants],
        item_count=counts.get(project.id, 0),
        children=[],
    )


def build_project_tree(session: Session) -> list[ProjectNode]:
    """Return root projects with nested children (roots = no parent)."""
    projects = project_repo.list_projects(session)
    counts = project_repo.item_counts_by_project(session)
    nodes = {p.id: _node(p, counts) for p in projects}

    roots: list[ProjectNode] = []
    for project in projects:
        node = nodes[project.id]
        if project.parent_id is not None and project.parent_id in nodes:
            nodes[project.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots
