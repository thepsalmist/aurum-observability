import pytest
from pydantic import ValidationError

from gateway.settings import Settings, get_settings


def test_settings_read_from_environment() -> None:
    settings = Settings()

    assert settings.s3_endpoint_url == "http://seaweedfs.test:8333"
    assert settings.s3_access_key == "test-access-key"
    assert settings.s3_secret_key.get_secret_value() == "test-secret-key"
    assert settings.s3_bucket == "test-bucket"
    assert settings.auth_token.get_secret_value() == "test-token"


def test_region_defaults_and_is_overridable(monkeypatch: pytest.MonkeyPatch) -> None:
    assert Settings().s3_region == "us-east-1"

    monkeypatch.setenv("SEAWEEDFS_S3_REGION", "eu-west-1")
    assert Settings().s3_region == "eu-west-1"


def test_auth_is_required_by_default() -> None:
    assert Settings().auth_required is True


@pytest.mark.parametrize("value", ["false", "0", "no"])
def test_auth_requirement_can_be_disabled(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("ARTIFACT_GATEWAY_AUTH_REQUIRED", value)

    assert Settings().auth_required is False


@pytest.mark.parametrize(
    "missing",
    [
        "SEAWEEDFS_S3_ENDPOINT_URL",
        "SEAWEEDFS_S3_ACCESS_KEY",
        "SEAWEEDFS_S3_SECRET_KEY",
        "SEAWEEDFS_BUCKET",
    ],
)
def test_missing_required_setting_is_rejected(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    monkeypatch.delenv(missing)

    with pytest.raises(ValidationError):
        Settings()


def test_secrets_are_not_exposed_by_repr() -> None:
    rendered = repr(Settings())

    assert "test-secret-key" not in rendered
    assert "test-token" not in rendered


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
