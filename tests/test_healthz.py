import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from gateway.main import app


def test_healthz_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_fails_when_settings_are_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SEAWEEDFS_BUCKET")

    with pytest.raises(ValidationError), TestClient(app):
        pass
