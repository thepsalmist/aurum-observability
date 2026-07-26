import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from gateway.main import app


def test_healthz_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_healthz_does_not_require_a_token() -> None:
    """Liveness probes must keep working without gateway credentials."""
    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200


def test_startup_fails_when_settings_are_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SEAWEEDFS_BUCKET")

    with pytest.raises(ValidationError), TestClient(app):
        pass


def test_startup_fails_when_auth_is_required_without_a_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ARTIFACT_GATEWAY_AUTH_TOKEN")

    with pytest.raises(ValidationError), TestClient(app):
        pass
