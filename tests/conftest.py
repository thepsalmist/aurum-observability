import pytest

from gateway.settings import Settings, get_settings

GATEWAY_ENV = {
    "SEAWEEDFS_S3_ENDPOINT_URL": "http://seaweedfs.test:8333",
    "SEAWEEDFS_S3_ACCESS_KEY": "test-access-key",
    "SEAWEEDFS_S3_SECRET_KEY": "test-secret-key",
    "SEAWEEDFS_BUCKET": "test-bucket",
    "ARTIFACT_GATEWAY_AUTH_TOKEN": "test-token",
}

OPTIONAL_ENV = (
    "SEAWEEDFS_S3_REGION",
    "ARTIFACT_GATEWAY_AUTH_REQUIRED",
)


@pytest.fixture(autouse=True)
def gateway_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate every test from the developer's real .env and shell environment."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for name in (*GATEWAY_ENV, *OPTIONAL_ENV):
        monkeypatch.delenv(name, raising=False)
    for name, value in GATEWAY_ENV.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
