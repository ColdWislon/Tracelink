"""Shared pytest fixtures.

Repository/API tests run against a real Postgres database (``tracelink_test`` by
default). Each test runs inside an outer transaction that is rolled back, with the
session joining via SAVEPOINTs so service-level ``commit()`` calls are isolated.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from app.core.db import get_session
from app.main import app
from app.models import Base
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

TEST_DATABASE_URL = os.environ.get(
    "TRACELINK_TEST_DATABASE_URL",
    "postgresql+psycopg://tracelink:tracelink@localhost:5432/tracelink_test",
)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    eng = create_engine(TEST_DATABASE_URL, future=True)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    connection = engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """A TestClient whose requests use the isolated test session."""

    def _override() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_session] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
