from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from gateway.main import app
from gateway.validation import (
    DEFAULT_ALLOWED_FILENAMES,
    RUN_ID_MAX_LENGTH,
    InvalidArtifactRequest,
    validate_filename,
    validate_run_id,
)


@pytest.mark.parametrize(
    "run_id",
    [
        "20260721-eurusd-m15",
        "0f8c2b1a4d5e4f7a9b3c6d8e1f2a3b4c",
        "run_42",
        "strategy.v1.2",
        "A",
        "a" * RUN_ID_MAX_LENGTH,
    ],
)
def test_valid_run_ids_are_accepted(run_id: str) -> None:
    assert validate_run_id(run_id) == run_id


@pytest.mark.parametrize(
    "run_id",
    [
        "../../etc/passwd",
        "..",
        "../run",
        "run/../other",
        "run/..",
        "a..b",
        "runs/nested",
        "/absolute",
        "run id",
        "run\tid",
        "run\nid",
        "run\x00id",
        "",
        ".hidden",
        "-leading-dash",
        "_leading-underscore",
        "run$id",
        "run%2e%2e",
        "run?query",
        "run#fragment",
        "s3://bucket/key",
        "a" * (RUN_ID_MAX_LENGTH + 1),
    ],
)
def test_invalid_run_ids_are_rejected(run_id: str) -> None:
    with pytest.raises(InvalidArtifactRequest):
        validate_run_id(run_id)


def test_decoded_traversal_is_rejected() -> None:
    """ASGI decodes %2e%2e%2f before the value reaches validation."""
    with pytest.raises(InvalidArtifactRequest):
        validate_run_id("../..")


@pytest.mark.parametrize("filename", sorted(DEFAULT_ALLOWED_FILENAMES))
def test_allowlisted_filenames_are_accepted(filename: str) -> None:
    assert validate_filename(filename, DEFAULT_ALLOWED_FILENAMES) == filename


@pytest.mark.parametrize(
    "filename",
    [
        "../../etc/passwd",
        "..",
        "../report.html",
        "runs/report.html",
        "report.html.bak",
        "REPORT.HTML",
        "report.htm",
        "secrets.env",
        "",
        "report.html\x00.png",
    ],
)
def test_disallowed_filenames_are_rejected(filename: str) -> None:
    with pytest.raises(InvalidArtifactRequest):
        validate_filename(filename, DEFAULT_ALLOWED_FILENAMES)


def test_filename_check_is_exact_match_against_the_allowlist() -> None:
    assert validate_filename("only.json", {"only.json"}) == "only.json"

    with pytest.raises(InvalidArtifactRequest):
        validate_filename("report.html", {"only.json"})


def test_error_messages_do_not_echo_the_rejected_value() -> None:
    """Avoid reflecting caller-controlled input back in responses."""
    payload = "<script>alert(1)</script>"

    with pytest.raises(InvalidArtifactRequest) as run_id_error:
        validate_run_id(payload)
    with pytest.raises(InvalidArtifactRequest) as filename_error:
        validate_filename(payload, DEFAULT_ALLOWED_FILENAMES)

    assert payload not in str(run_id_error.value)
    assert payload not in str(filename_error.value)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Exercise the real app's exception handler via a temporary route."""
    original_routes = list(app.router.routes)

    @app.get("/_validate/{run_id}")
    def _validate(run_id: str) -> dict[str, str]:
        return {"run_id": validate_run_id(run_id)}

    with TestClient(app) as test_client:
        yield test_client

    app.router.routes[:] = original_routes


def test_invalid_run_id_returns_400(client: TestClient) -> None:
    response = client.get("/_validate/run%20id")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Run ID is not a valid artifact run identifier."
    }


@pytest.mark.parametrize(
    "path",
    [
        "/_validate/%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "/_validate/..%2f..%2fetc%2fpasswd",
        "/_validate/%2E%2E",
        "/_validate/..",
        "/_validate/a%2Fb",
        "/_validate/%2fetc%2fpasswd",
    ],
)
def test_traversal_attempts_never_succeed(client: TestClient, path: str) -> None:
    """Two layers stop traversal, and neither may fail open.

    Values that decode to a path separator never match the `{run_id}` converter
    (Starlette matches `[^/]+` against the already-decoded path), so they 404 at
    routing. Anything that does reach the handler is rejected by validation as 400.
    """
    response = client.get(path)

    assert response.status_code in {400, 404}


def test_decoded_dots_reach_validation_and_return_400(client: TestClient) -> None:
    response = client.get("/_validate/%2E%2E")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Run ID is not a valid artifact run identifier."
    }


def test_valid_run_id_passes_through(client: TestClient) -> None:
    response = client.get("/_validate/20260721-eurusd-m15")

    assert response.status_code == 200
    assert response.json() == {"run_id": "20260721-eurusd-m15"}
