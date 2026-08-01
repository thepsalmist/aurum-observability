import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from gateway.settings import get_settings

logger = logging.getLogger(__name__)

OBJECT_KEY_ROOT = "runs"
STREAM_CHUNK_SIZE = 64 * 1024

MISSING_OBJECT_ERROR_CODES = frozenset({"NoSuchKey", "NotFound", "404"})
MISSING_BUCKET_ERROR_CODE = "NoSuchBucket"


class ArtifactNotFound(Exception):
    """Raised when the requested object does not exist in storage."""


class ArtifactStorageUnavailable(Exception):
    """Raised when the object store cannot be reached or fails the request."""


@dataclass(frozen=True)
class ArtifactObject:
    content_type: str | None
    content_length: int | None
    etag: str | None
    last_modified: datetime | None
    chunks: Iterator[bytes]


def build_object_key(profile: str, run_id: str, filename: str) -> str:
    """Map a request to its storage key. Segments must already be validated."""
    return f"{OBJECT_KEY_ROOT}/{profile}/{run_id}/{filename}"


@lru_cache
def get_s3_client() -> BaseClient:
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
        region_name=settings.s3_region,
        config=Config(
            s3={"addressing_style": "path"},
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )


def fetch_artifact(key: str) -> ArtifactObject:
    """Open a streaming read of an object, or raise if it is missing or unreachable."""
    settings = get_settings()
    client = get_s3_client()

    try:
        response = client.get_object(Bucket=settings.s3_bucket, Key=key)
    except ClientError as error:
        code = str(error.response.get("Error", {}).get("Code", ""))
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code == MISSING_BUCKET_ERROR_CODE:
            logger.error("Artifact bucket %s does not exist", settings.s3_bucket)
            raise ArtifactStorageUnavailable from error
        if code in MISSING_OBJECT_ERROR_CODES or status == 404:
            logger.info("Artifact not found: %s", key)
            raise ArtifactNotFound from error
        logger.warning("Artifact storage error for %s: %s", key, code)
        raise ArtifactStorageUnavailable from error
    except BotoCoreError as error:
        logger.warning(
            "Artifact storage unreachable for %s: %s", key, type(error).__name__
        )
        raise ArtifactStorageUnavailable from error

    body = response["Body"]

    def chunks() -> Iterator[bytes]:
        try:
            yield from body.iter_chunks(STREAM_CHUNK_SIZE)
        finally:
            body.close()

    return ArtifactObject(
        content_type=response.get("ContentType"),
        content_length=response.get("ContentLength"),
        etag=response.get("ETag"),
        last_modified=response.get("LastModified"),
        chunks=chunks(),
    )
