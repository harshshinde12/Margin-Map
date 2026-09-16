"""Shared pytest fixtures (Phase 8)."""

from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)
