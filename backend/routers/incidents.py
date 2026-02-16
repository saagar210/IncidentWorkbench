"""Incident management router."""

import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from database import db
from models.api import IncidentListResponse, IncidentResponse
from models.incident import Incident, IncidentSource, Severity
from models.report import MetricsResult
from security.auth import AuthUser, require_roles_dependency
from services.metrics import MetricsCalculator

router = APIRouter(prefix="/incidents", tags=["incidents"])
AdminUser = Annotated[AuthUser, Depends(require_roles_dependency({"admin"}))]


@router.get("")
async def list_incidents(
    source: IncidentSource | None = None,
    severity: Severity | None = None,
    offset: Annotated[int, Query(ge=0, le=9_223_372_036_854_775_807)] = 0,
    limit: Annotated[int, Query(ge=1, le=1_000)] = 100,
) -> IncidentListResponse:
    """List all incidents with optional filters."""
    conn = db.get_connection()
    try:
        # Build query with filters
        query = "SELECT * FROM incidents WHERE 1=1"
        params: list[object] = []

        if source:
            query += " AND source = ?"
            params.append(source.value)

        if severity:
            query += " AND severity = ?"
            params.append(severity.value)

        # Add ordering and pagination
        query += " ORDER BY occurred_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # Execute query
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        # Convert rows to Incident models
        incidents = []
        for row in rows:
            incidents.append(
                Incident(
                    id=row["id"],
                    external_id=row["external_id"],
                    source=IncidentSource(row["source"]),
                    severity=Severity(row["severity"]),
                    title=row["title"],
                    description=row["description"] or "",
                    occurred_at=datetime.fromisoformat(row["occurred_at"]),
                    resolved_at=datetime.fromisoformat(row["resolved_at"])
                    if row["resolved_at"]
                    else None,
                    raw_data=json.loads(row["raw_data"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )

        # Get total count
        count_query = "SELECT COUNT(*) as count FROM incidents WHERE 1=1"
        count_params: list[object] = []

        if source:
            count_query += " AND source = ?"
            count_params.append(source.value)

        if severity:
            count_query += " AND severity = ?"
            count_params.append(severity.value)

        total = conn.execute(count_query, count_params).fetchone()["count"]

        return IncidentListResponse(
            incidents=incidents,
            total=total,
            severity_filter=severity,
        )
    finally:
        conn.close()


@router.get("/metrics", response_model=MetricsResult)
async def get_metrics(
    source: IncidentSource | None = None,
    severity: Severity | None = None,
) -> MetricsResult:
    """Calculate metrics for all or filtered incidents."""
    conn = db.get_connection()
    try:
        calc = MetricsCalculator(conn)

        # Build query to get incident IDs with filters
        where_clauses = []
        params = []
        if source:
            where_clauses.append("source = ?")
            params.append(source.value)
        if severity:
            where_clauses.append("severity = ?")
            params.append(severity.value)

        # Safe: where_clauses contains only literal strings "source = ?" and "severity = ?"
        # The params tuple contains the actual user input which is safely parameterized
        where_sql = " AND ".join(where_clauses) if where_clauses else ""
        query = f"SELECT id FROM incidents {('WHERE ' + where_sql) if where_sql else ''}"

        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        incident_ids = [r["id"] for r in rows] if rows else None

        return calc.calculate(incident_ids)
    finally:
        conn.close()


@router.get("/{incident_id}", responses={404: {"description": "Incident not found"}})
async def get_incident(
    incident_id: Annotated[int, Path(ge=1, le=9_223_372_036_854_775_807)],
) -> IncidentResponse:
    """Get a specific incident by ID."""
    conn = db.get_connection()
    try:
        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Incident not found")

        incident = Incident(
            id=row["id"],
            external_id=row["external_id"],
            source=IncidentSource(row["source"]),
            severity=Severity(row["severity"]),
            title=row["title"],
            description=row["description"] or "",
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
            raw_data=json.loads(row["raw_data"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

        return IncidentResponse(incident=incident)
    finally:
        conn.close()


@router.delete("")
async def delete_all_incidents(current_user: AdminUser) -> dict:
    """Delete all incidents from the database."""
    del current_user
    conn = db.get_connection()
    try:
        cursor = conn.execute("DELETE FROM incidents")
        deleted = cursor.rowcount
        conn.commit()
        return {"deleted": deleted, "message": f"Deleted {deleted} incidents"}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
