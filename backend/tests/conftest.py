"""Fresh SQLite databases and a stopped simulator for every test."""

from __future__ import annotations

import os

os.environ["SIM_AUTOSTART"] = "0"

import pytest


@pytest.fixture(autouse=True)
def _stop_simulator_after_test():
    yield
    from app.services.simulator import engine

    engine.reset_runtime()


@pytest.fixture
def db_session(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + (tmp_path / "unit.db").as_posix())
    monkeypatch.setenv("SIM_AUTOSTART", "0")
    from app.database import get_session, init_db, reset_connection
    from app.services.simulator import engine

    engine.reset_runtime()
    reset_connection()
    init_db()
    session = get_session()
    try:
        yield session
    finally:
        session.close()
        engine.reset_runtime()
        reset_connection()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + (tmp_path / "api.db").as_posix())
    monkeypatch.setenv("SIM_AUTOSTART", "0")
    from fastapi.testclient import TestClient

    from app.database import reset_connection
    from app.main import app
    from app.services.simulator import engine

    engine.reset_runtime()
    reset_connection()
    with TestClient(app) as test_client:
        yield test_client
    engine.reset_runtime()
    reset_connection()
