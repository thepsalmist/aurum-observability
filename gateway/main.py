import mimetypes
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timezone
from email.utils import format_datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from gateway.auth import require_token
from gateway.settings import Settings, get_settings
from gateway.storage import (
    ArtifactNotFound,
    ArtifactObject,
    ArtifactStorageUnavailable,
    build_object_key,
    fetch_artifact,
)
from gateway.validation import (
    InvalidArtifactRequest,
    validate_filename,
    validate_profile,
    validate_run_id,
)

GENERIC_CONTENT_TYPES = frozenset({"binary/octet-stream", "application/octet-stream"})
FALLBACK_CONTENT_TYPE = "application/octet-stream"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_settings()
    yield


app = FastAPI(
    title="Aurum Artifact Gateway",
    version="0.1.0",
    lifespan=lifespan,
)


async def invalid_artifact_request_handler(
    request: Request, exc: InvalidArtifactRequest
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
    )


async def artifact_not_found_handler(
    request: Request, exc: ArtifactNotFound
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Artifact not found."}
    )


async def artifact_storage_unavailable_handler(
    request: Request, exc: ArtifactStorageUnavailable
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Artifact storage is unavailable."},
    )


app.add_exception_handler(InvalidArtifactRequest, invalid_artifact_request_handler)  # type: ignore[arg-type]
app.add_exception_handler(ArtifactNotFound, artifact_not_found_handler)  # type: ignore[arg-type]
app.add_exception_handler(
    ArtifactStorageUnavailable, artifact_storage_unavailable_handler
)  # type: ignore[arg-type]


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


def _content_type_for(artifact: ArtifactObject, filename: str) -> str:
    stored = artifact.content_type
    if stored and stored not in GENERIC_CONTENT_TYPES:
        return stored
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or FALLBACK_CONTENT_TYPE


def _response_headers(artifact: ArtifactObject) -> dict[str, str]:
    headers = {"X-Content-Type-Options": "nosniff"}
    if artifact.content_length is not None:
        headers["Content-Length"] = str(artifact.content_length)
    if artifact.etag:
        headers["ETag"] = artifact.etag
    if artifact.last_modified is not None:
        as_utc = artifact.last_modified.astimezone(timezone.utc)
        headers["Last-Modified"] = format_datetime(as_utc, usegmt=True)
    return headers


@app.get(
    "/artifacts/runs/{profile}/{run_id}/{filename}",
    dependencies=[Depends(require_token)],
)
def get_artifact(
    profile: str,
    run_id: str,
    filename: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> StreamingResponse:
    validate_profile(profile)
    validate_run_id(run_id)
    validate_filename(filename, settings.allowed_filenames)

    artifact = fetch_artifact(build_object_key(profile, run_id, filename))

    return StreamingResponse(
        artifact.chunks,
        media_type=_content_type_for(artifact, filename),
        headers=_response_headers(artifact),
    )
