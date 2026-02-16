"""OpenTelemetry bootstrap helpers."""

from __future__ import annotations

from fastapi import FastAPI


def setup_observability(app: FastAPI):
    """Best-effort OpenTelemetry wiring.

    If OTel dependencies are unavailable, this is intentionally a no-op.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except Exception:
        return None

    FastAPIInstrumentor.instrument_app(app)
    return trace.get_tracer("incident-workbench")
