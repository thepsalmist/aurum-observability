from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from gateway.settings import get_settings
from gateway.validation import InvalidArtifactRequest


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


app.add_exception_handler(InvalidArtifactRequest, invalid_artifact_request_handler)  # type: ignore[arg-type]


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
