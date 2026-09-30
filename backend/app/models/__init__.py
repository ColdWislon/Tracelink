"""SQLAlchemy ORM models.

Importing this package must import every model module so that
``Base.metadata`` is fully populated (used by Alembic autogenerate).
Model modules are added in Phase 1.1.
"""

from app.core.db import Base

__all__ = ["Base"]
