from collections.abc import Iterator

import boto3
import pytest
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import EndpointConnectionError
from fastapi.testclient import TestClient
from moto import mock_aws

from gateway.main import app
from gateway.settings import get_settings
from gateway.storage import (
    STREAM_CHUNK_SIZE,
    build_object_key,
    fetch_artifact,
    get_s3_client,
)

PROFILE = "jpy_benchmark"
RUN_ID = "100cd43sed"
AUTH = {"Authorization": "Bearer test-token"}
REPORT_BODY = b"<html><body>backtest report</body></html>"


def artifact_url(
    profile: str = PROFILE, run_id: str = RUN_ID, filename: str = "report.html"
) -> str:
    return f"/artifacts/runs/{profile}/{run_id}/{filename}"


@pytest.fixture
def s3() -> Iterator[BaseClient]:
    with mock_aws():
        settings = get_settings()
        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            region_name=settings.s3_region,
            config=Config(s3={"addressing_style": "path"}),
        )
        client.create_bucket(Bucket=settings.s3_bucket)
        yield client


@pytest.fixture
def client(s3: BaseClient) -> Iterator[TestClient]:
    settings = get_settings()
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=build_object_key(PROFILE, RUN_ID, "report.html"),
        Body=REPORT_BODY,
        ContentType="text/html",
    )
    with TestClient(app) as test_client:
        yield test_client


def test_object_key_layout_matches_storage() -> None:
    assert build_object_key(PROFILE, RUN_ID, "report.html") == (
        "runs/jpy_benchmark/100cd43sed/report.html"
    )


def test_artifact_is_served(client: TestClient) -> None:
    response = client.get(artifact_url(), headers=AUTH)

    assert response.status_code == 200
    assert response.content == REPORT_BODY
    assert response.headers["content-type"].startswith("text/html")


def test_response_carries_storage_metadata(client: TestClient) -> None:
    response = client.get(artifact_url(), headers=AUTH)

    assert response.headers["content-length"] == str(len(REPORT_BODY))
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "etag" in response.headers
    assert "last-modified" in response.headers


@pytest.mark.parametrize(
    ("filename", "expected_type"),
    [
        ("summary.json", "application/json"),
        ("trades.csv", "text/csv"),
        ("equity_curve.png", "image/png"),
    ],
)
def test_content_type_is_guessed_when_storage_is_unhelpful(
    client: TestClient, s3: BaseClient, filename: str, expected_type: str
) -> None:
    """SeaweedFS stores binary/octet-stream when the publisher omits a type."""
    s3.put_object(
        Bucket=get_settings().s3_bucket,
        Key=build_object_key(PROFILE, RUN_ID, filename),
        Body=b"payload",
        ContentType="binary/octet-stream",
    )

    response = client.get(artifact_url(filename=filename), headers=AUTH)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(expected_type)


def test_large_artifact_streams_intact(client: TestClient, s3: BaseClient) -> None:
    body = bytes(range(256)) * 4096

    s3.put_object(
        Bucket=get_settings().s3_bucket,
        Key=build_object_key(PROFILE, RUN_ID, "drawdown.png"),
        Body=body,
    )

    with client.stream(
        "GET", artifact_url(filename="drawdown.png"), headers=AUTH
    ) as response:
        assert response.status_code == 200
        streamed = b"".join(response.iter_bytes())

    assert streamed == body


def test_body_is_read_in_chunks_rather_than_all_at_once(s3: BaseClient) -> None:
    body = b"x" * (STREAM_CHUNK_SIZE * 3)
    key = build_object_key(PROFILE, RUN_ID, "trades.csv")
    s3.put_object(Bucket=get_settings().s3_bucket, Key=key, Body=body)

    chunks = list(fetch_artifact(key).chunks)

    assert len(chunks) > 1
    assert b"".join(chunks) == body


def test_missing_object_returns_404(client: TestClient) -> None:
    response = client.get(artifact_url(run_id="does-not-exist"), headers=AUTH)

    assert response.status_code == 404
    assert response.json() == {"detail": "Artifact not found."}


def test_unknown_profile_returns_404(client: TestClient) -> None:
    response = client.get(artifact_url(profile="gold"), headers=AUTH)

    assert response.status_code == 404


def test_missing_bucket_is_a_gateway_fault_not_a_missing_artifact(
    s3: BaseClient,
) -> None:
    """A deleted bucket answers with HTTP 404, but it is a deployment fault."""
    settings = get_settings()
    s3.delete_bucket(Bucket=settings.s3_bucket)

    with TestClient(app) as test_client:
        response = test_client.get(artifact_url(), headers=AUTH)

    assert response.status_code == 502
    assert response.json() == {"detail": "Artifact storage is unavailable."}


def test_unreachable_storage_returns_502(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class UnreachableClient:
        def get_object(self, **kwargs: object) -> object:
            raise EndpointConnectionError(endpoint_url="http://seaweedfs.test:8333")

    monkeypatch.setattr("gateway.storage.get_s3_client", lambda: UnreachableClient())

    response = client.get(artifact_url(), headers=AUTH)

    assert response.status_code == 502
    assert response.json() == {"detail": "Artifact storage is unavailable."}


def test_request_without_token_is_rejected(client: TestClient) -> None:
    response = client.get(artifact_url())

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_request_with_wrong_token_is_rejected(client: TestClient) -> None:
    response = client.get(artifact_url(), headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401


def test_auth_is_checked_before_validation(client: TestClient) -> None:
    """An unauthenticated caller learns nothing about what the gateway accepts."""
    response = client.get(artifact_url(run_id="not a valid id"))

    assert response.status_code == 401


def test_artifact_is_served_when_auth_is_disabled(
    monkeypatch: pytest.MonkeyPatch, s3: BaseClient
) -> None:
    monkeypatch.setenv("ARTIFACT_GATEWAY_AUTH_REQUIRED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=build_object_key(PROFILE, RUN_ID, "report.html"),
        Body=REPORT_BODY,
    )

    with TestClient(app) as test_client:
        response = test_client.get(artifact_url())

    assert response.status_code == 200
    assert response.content == REPORT_BODY


@pytest.mark.parametrize("profile", ["not a profile", ".hidden", "-dash", "gold$"])
def test_invalid_profile_returns_400(client: TestClient, profile: str) -> None:
    response = client.get(artifact_url(profile=profile), headers=AUTH)

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Profile is not a valid artifact profile name."
    }


def test_overlong_profile_returns_400(client: TestClient) -> None:
    response = client.get(artifact_url(profile="a" * 129), headers=AUTH)

    assert response.status_code == 400
    assert response.json() == {"detail": "Profile is too long."}


def test_seaweedfs_is_addressed_by_path_not_bucket_hostname() -> None:
    assert get_s3_client().meta.config.s3["addressing_style"] == "path"


@pytest.mark.parametrize("run_id", ["not a run", "$run", "_leading"])
def test_invalid_run_id_returns_400(client: TestClient, run_id: str) -> None:
    response = client.get(artifact_url(run_id=run_id), headers=AUTH)

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Run ID is not a valid artifact run identifier."
    }


@pytest.mark.parametrize(
    "filename", ["secrets.env", "report.html.bak", "REPORT.HTML", "id_rsa"]
)
def test_disallowed_filename_returns_400(client: TestClient, filename: str) -> None:
    response = client.get(artifact_url(filename=filename), headers=AUTH)

    assert response.status_code == 400
    assert response.json() == {"detail": "Artifact filename is not allowed."}


@pytest.mark.parametrize(
    "path",
    [
        "/artifacts/runs/jpy/%2e%2e%2f%2e%2e%2fetc%2fpasswd/report.html",
        "/artifacts/runs/jpy/..%2f..%2fetc/report.html",
        "/artifacts/runs/%2E%2E/%2E%2E/report.html",
        "/artifacts/runs/jpy/100cd43sed/..%2f..%2fsecrets.env",
        "/artifacts/runs/jpy/100cd43sed/%2e%2e%2fsummary.json",
        "/artifacts/runs/../../etc/passwd",
    ],
)
def test_traversal_attempts_never_reach_storage(client: TestClient, path: str) -> None:
    response = client.get(path, headers=AUTH)

    assert response.status_code in {400, 404}


def test_validation_runs_before_any_storage_access(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_if_called(key: str) -> None:
        raise AssertionError(f"storage was accessed for {key}")

    monkeypatch.setattr("gateway.main.fetch_artifact", fail_if_called)

    assert (
        client.get(artifact_url(filename="secrets.env"), headers=AUTH).status_code
        == 400
    )
    assert client.get(artifact_url(run_id="bad id"), headers=AUTH).status_code == 400
    assert client.get(artifact_url(profile="bad id"), headers=AUTH).status_code == 400
