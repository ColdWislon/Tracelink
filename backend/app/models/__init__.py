"""SQLAlchemy ORM models.

Importing this package imports every model module so that ``Base.metadata`` is
fully populated (used by Alembic autogenerate and by table creation in tests).
"""

from app.core.db import Base
from app.models.audit import AuditLog
from app.models.baseline import Baseline, BaselineEntry
from app.models.evidence import Evidence, EvidenceResult, RegressionRun
from app.models.item import Item, ItemRevision, Link
from app.models.project import IpReference, ItemType, Project, Variant
from app.models.review import Comment, Review, ReviewAssignment

__all__ = [
    "Base",
    "AuditLog",
    "Baseline",
    "BaselineEntry",
    "Comment",
    "Evidence",
    "EvidenceResult",
    "IpReference",
    "Item",
    "ItemRevision",
    "ItemType",
    "Link",
    "Project",
    "RegressionRun",
    "Review",
    "ReviewAssignment",
    "Variant",
]
