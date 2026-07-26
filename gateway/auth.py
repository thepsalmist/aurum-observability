import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from gateway.settings import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="ArtifactGatewayToken")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid artifact gateway token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Reject requests that do not carry the configured bearer token."""
    if not settings.auth_required:
        return

    if credentials is None:
        raise _unauthorized()

    # Settings validation guarantees a non-blank token whenever auth is required.
    expected = settings.auth_token.get_secret_value()  # type: ignore[union-attr]
    if not secrets.compare_digest(
        credentials.credentials.encode("utf-8"), expected.encode("utf-8")
    ):
        raise _unauthorized()
