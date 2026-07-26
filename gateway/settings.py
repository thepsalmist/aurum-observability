from functools import lru_cache
from typing import Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
