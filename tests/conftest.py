import os

import pytest

from gateway.settings import Settings, get_settings
from gateway.storage import get_s3_client

S3_ENDPOINT_URL = "http://seaweedfs.test:8333"

GATEWAY_ENV = {
    "SEAWEEDFS_S3_ENDPOINT_URL": S3_ENDPOINT_URL,
    "SEAWEEDFS_S3_ACCESS_KEY": "test-access-key",
    "SEAWEEDFS_S3_SECRET_KEY": "test-secret-key",
    "SEAWEEDFS_BUCKET": "test-bucket",
    "ARTIFACT_GATEWAY_AUTH_TOKEN": "test-token",
}

OPTIONAL_ENV = (
    "SEAWEEDFS_S3_REGION",
    "ARTIFACT_GATEWAY_AUTH_REQUIRED",
)


def pytest_configure(config: pytest.Config) -> None:
    # moto registers S3-compatible endpoints when it is imported, which collection does.
    os.environ["MOTO_S3_CUSTOM_ENDPOINTS"] = S3_ENDPOINT_URL


@pytest.fixture(autouse=True)
def gateway_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate every test from the developer's real .env and shell environment."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for name in (*GATEWAY_ENV, *OPTIONAL_ENV):
        monkeypatch.delenv(name, raising=False)
    for name, value in GATEWAY_ENV.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    get_s3_client.cache_clear()
    yield
    get_settings.cache_clear()
    get_s3_client.cache_clear()
