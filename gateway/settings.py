from functools import lru_cache
from typing import Annotated, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from gateway.validation import DEFAULT_ALLOWED_FILENAMES, is_safe_name


class Settings(BaseSettings):
    """Artifact gateway configuration, read from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    s3_endpoint_url: str = Field(alias="SEAWEEDFS_S3_ENDPOINT_URL")
    s3_access_key: str = Field(alias="SEAWEEDFS_S3_ACCESS_KEY")
    s3_secret_key: SecretStr = Field(alias="SEAWEEDFS_S3_SECRET_KEY")
    s3_bucket: str = Field(alias="SEAWEEDFS_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="SEAWEEDFS_S3_REGION")

    auth_required: bool = Field(default=True, alias="ARTIFACT_GATEWAY_AUTH_REQUIRED")
    auth_token: SecretStr | None = Field(
        default=None, alias="ARTIFACT_GATEWAY_AUTH_TOKEN"
    )

    allowed_filenames: Annotated[frozenset[str], NoDecode] = Field(
        default=DEFAULT_ALLOWED_FILENAMES,
        alias="ARTIFACT_GATEWAY_ALLOWED_FILENAMES",
    )

    @field_validator("allowed_filenames", mode="before")
    @classmethod
    def _split_allowed_filenames(cls, value: object) -> object:
        if isinstance(value, str):
            return frozenset(part.strip() for part in value.split(",") if part.strip())
        return value

    @field_validator("allowed_filenames", mode="after")
    @classmethod
    def _check_allowed_filenames(cls, value: frozenset[str]) -> frozenset[str]:
        if not value:
            raise ValueError("ARTIFACT_GATEWAY_ALLOWED_FILENAMES must not be empty")
        unsafe = sorted(name for name in value if not is_safe_name(name))
        if unsafe:
            raise ValueError(
                "ARTIFACT_GATEWAY_ALLOWED_FILENAMES contains unsafe entries: "
                f"{', '.join(unsafe)}"
            )
        return value

    @model_validator(mode="after")
    def _check_auth_token_present(self) -> Self:
        if self.auth_required and not (
            self.auth_token and self.auth_token.get_secret_value().strip()
        ):
            raise ValueError(
                "ARTIFACT_GATEWAY_AUTH_TOKEN must be a non-blank value when "
                "ARTIFACT_GATEWAY_AUTH_REQUIRED is true"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
