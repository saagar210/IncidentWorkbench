"""FastAPI application entry point."""

import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import db
from exceptions import WorkbenchError
from routers import clusters, health, incidents, ingest, reports, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Run database migrations
    print("Running database migrations...")
    db.run_migrations()
    print("Database migrations complete")

    yield

    # Shutdown: Cleanup if needed
    pass


# Create FastAPI app
app = FastAPI(
    title="Incident Workbench API",
    description="Backend API for incident analysis and clustering",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "tauri://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(settings.router)
app.include_router(ingest.router)
app.include_router(incidents.router)
app.include_router(clusters.router)
app.include_router(reports.router)


# Exception handler for WorkbenchError
@app.exception_handler(WorkbenchError)
async def workbench_exception_handler(request: Request, exc: WorkbenchError):
    """Handle WorkbenchError exceptions with user-friendly messages."""
    status_code = 500

    # Map specific exceptions to HTTP status codes
    from exceptions import (
        InsufficientDataError,
        JiraConnectionError,
        JiraQueryError,
        OllamaModelNotFoundError,
        OllamaUnavailableError,
        SlackAPIError,
        ReportGenerationError,
    )

    if isinstance(exc, OllamaUnavailableError):
        status_code = 503
    elif isinstance(exc, OllamaModelNotFoundError):
        status_code = 503
    elif isinstance(exc, (JiraConnectionError, SlackAPIError)):
        status_code = 502  # Bad Gateway (upstream service issue)
    elif isinstance(exc, JiraQueryError):
        status_code = 422  # Unprocessable Entity
    elif isinstance(exc, InsufficientDataError):
        status_code = 422
    elif isinstance(exc, ReportGenerationError):
        status_code = 500

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": exc.message,
            "error_type": exc.__class__.__name__,
            "details": exc.details,
        },
    )


if __name__ == "__main__":
    import uvicorn

    # Use port 0 to let the OS assign a free port
    # This eliminates the race condition between find_free_port() and uvicorn.run()
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=0,  # Let OS choose a free port
        log_level="info",
    )
    server = uvicorn.Server(config)

    # Note: The actual bound port can be retrieved after server.run() starts,
    # but that happens asynchronously. For now, we still use the hardcoded port
    # approach in Tauri. A full fix would require reading stdout from the sidecar.
    # Fallback to hardcoded port for compatibility
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        # Allow explicit port override for development
        port = int(sys.argv[2])
        print(port)
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    else:
        # Production: use fixed port to avoid stdout parsing complexity
        port = 8765
        print(port)
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
