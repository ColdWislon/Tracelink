"""FastAPI dependencies: database session and the current-user seam."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_session


def get_current_user() -> str:
    """Return the acting user. Single local user until the pluggable auth layer lands."""
    return settings.current_user


SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[str, Depends(get_current_user)]
