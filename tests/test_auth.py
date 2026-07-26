from collections.abc import Iterator

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from gateway.auth import require_token


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(require_token)])
    def protected() -> dict[str, str]:
        return {"status": "authorized"}

    with TestClient(app) as test_client:
        yield test_client


def test_valid_token_is_accepted(client: TestClient) -> None:
    response = client.get("/protected", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json() == {"status": "authorized"}


def test_bearer_scheme_is_case_insensitive(client: TestClient) -> None:
    response = client.get("/protected", headers={"Authorization": "bearer test-token"})

    assert response.status_code == 200


def test_missing_header_is_rejected(client: TestClient) -> None:
    response = client.get("/protected")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_wrong_token_is_rejected(client: TestClient) -> None:
    response = client.get("/protected", headers={"Authorization": "Bearer wrong-token"})

    assert response.status_code == 401


@pytest.mark.parametrize(
    "header",
    [
        "Basic test-token",
        "test-token",
        "Bearer",
        "Bearer ",
        "",
    ],
)
def test_malformed_authorization_headers_are_rejected(
    client: TestClient, header: str
) -> None:
    response = client.get("/protected", headers={"Authorization": header})

    assert response.status_code == 401


def test_token_prefix_is_not_accepted(client: TestClient) -> None:
    """A token that is a prefix of the real one must not pass."""
    response = client.get("/protected", headers={"Authorization": "Bearer test-"})

    assert response.status_code == 401


def test_non_ascii_configured_token_rejects_cleanly(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    """A non-ASCII configured token must yield 401, not a comparison error.

    HTTP header values are ASCII, so such a token can never be matched by a real
    request, but comparing it as `str` would raise TypeError and surface as a 500.
    """
    monkeypatch.setenv("ARTIFACT_GATEWAY_AUTH_TOKEN", "tökèn-ünicode")

    response = client.get("/protected", headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401


def test_auth_can_be_disabled(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    monkeypatch.setenv("ARTIFACT_GATEWAY_AUTH_REQUIRED", "false")

    assert client.get("/protected").status_code == 200
    assert (
        client.get("/protected", headers={"Authorization": "Bearer wrong"}).status_code
        == 200
    )


def test_response_body_does_not_leak_the_expected_token(client: TestClient) -> None:
    response = client.get("/protected", headers={"Authorization": "Bearer wrong-token"})

    assert "test-token" not in response.text
