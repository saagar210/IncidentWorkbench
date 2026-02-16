"""Contract tests backed by the OpenAPI schema."""

from __future__ import annotations

import warnings

import pytest

from main import app

pytestmark = pytest.mark.contract

# Schemathesis <4 still triggers jsonschema deprecation warnings during import.
# Keep contract output signal-focused until upstream dependencies catch up.
warnings.filterwarnings(
    "ignore",
    message=r"jsonschema.exceptions.RefResolutionError is deprecated.*",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"jsonschema.RefResolver is deprecated.*",
    category=DeprecationWarning,
)


def test_openapi_contract_baseline() -> None:
    """Always enforce a minimal contract baseline even when schemathesis is unavailable."""
    spec = app.openapi()
    assert "paths" in spec
    assert "/v1/health" in spec["paths"]
    assert "/v1/incidents" in spec["paths"]


try:
    import schemathesis

    schema = schemathesis.from_asgi("/openapi.json", app)
    health_schema = schema.clone().include(path="/v1/health", method="GET")
    incidents_schema = schema.clone().include(path_regex=r"^/v1/incidents(?:/.*)?$", method="GET")

    @health_schema.parametrize()
    def test_contract_health(case) -> None:
        response = case.call()
        case.validate_response(response)

    @incidents_schema.parametrize()
    def test_contract_incidents(case) -> None:
        response = case.call()
        case.validate_response(response)

except Exception as exc:  # pragma: no cover - compatibility guard for OpenAPI 3.1 tooling lag
    schemathesis_error = str(exc)

    def test_schemathesis_unavailable() -> None:
        pytest.skip(f"Schemathesis dynamic checks skipped: {schemathesis_error}")
