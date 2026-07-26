import re
from collections.abc import Collection

RUN_ID_MAX_LENGTH = 128

# Deliberately excludes "/" and any path separator, so a validated name is always a
# single path segment. Mirrors the object_key CHECK constraint on backtest_artifacts.
SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

DEFAULT_ALLOWED_FILENAMES = frozenset(
    {
        "report.html",
        "summary.json",
        "metrics.json",
        "trades.csv",
        "equity_curve.png",
        "drawdown.png",
    }
)


class InvalidArtifactRequest(ValueError):
    """Raised when a requested run ID or filename fails validation."""


def is_safe_name(value: str) -> bool:
    """Whether a value is a single, traversal-free path segment."""
    return ".." not in value and SAFE_NAME_PATTERN.fullmatch(value) is not None


def validate_run_id(run_id: str) -> str:
    if len(run_id) > RUN_ID_MAX_LENGTH:
        raise InvalidArtifactRequest("Run ID is too long.")
    if not is_safe_name(run_id):
        raise InvalidArtifactRequest("Run ID is not a valid artifact run identifier.")
    return run_id


def validate_filename(filename: str, allowed_filenames: Collection[str]) -> str:
    if filename not in allowed_filenames:
        raise InvalidArtifactRequest("Artifact filename is not allowed.")
    return filename
