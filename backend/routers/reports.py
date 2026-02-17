"""Report generation router."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from database import db
from exceptions import OllamaModelNotFoundError, OllamaUnavailableError
from models.api import ReportGenerateRequest
from models.cluster import ClusterResult
from models.report import MetricsResult, ReportResult
from security.auth import AuthUser, require_roles_dependency
from services.docx_generator import DocxGenerator
from services.metrics import MetricsCalculator
from services.ollama_client import OllamaClient
from services.summarizer import ClusterSummarizer

router = APIRouter(prefix="/reports", tags=["reports"])
AdminUser = Annotated[AuthUser, Depends(require_roles_dependency({"admin"}))]


def _fallback_executive_summary(
    quarter: str,
    metrics: MetricsResult,
    clusters: list[ClusterResult],
    error: Exception,
) -> str:
    """Generate deterministic summary text when Ollama is unavailable."""
    top_cluster = max(clusters, key=lambda c: c.size, default=None)
    top_cluster_text = (
        f"Top cluster: {top_cluster.summary or f'Cluster {top_cluster.cluster_id}'} "
        f"({top_cluster.size} incidents)."
        if top_cluster
        else "No clusters were available for summarization."
    )

    return (
        f"{quarter} incident summary generated without Ollama due to: {error}.\n\n"
        f"Total incidents: {metrics.total_incidents}. "
        f"SEV1: {metrics.sev1_count}, SEV2: {metrics.sev2_count}, "
        f"SEV3: {metrics.sev3_count}, SEV4: {metrics.sev4_count}.\n\n"
        f"Mean resolution (hours): {metrics.mean_resolution_hours}. "
        f"P90 resolution (hours): {metrics.p90_resolution_hours}.\n\n"
        f"{top_cluster_text}"
    )


@router.post("/generate")
async def generate_report(request: ReportGenerateRequest, current_user: AdminUser) -> dict:
    """Generate a Word document report for a cluster run."""
    del current_user
    conn = db.get_connection()

    try:
        # Verify cluster run exists
        cursor = conn.execute(
            "SELECT id FROM cluster_runs WHERE id = ?",
            (request.cluster_run_id,),
        )
        run_row = cursor.fetchone()
        if not run_row:
            raise HTTPException(status_code=404, detail="Cluster run not found")

        run_id = run_row["id"]

        # Get clusters for this run
        cursor = conn.execute(
            """
            SELECT id, cluster_label, summary, centroid_text
            FROM clusters
            WHERE run_id = ?
            ORDER BY id
            """,
            (run_id,),
        )
        cluster_rows = cursor.fetchall()

        # Build cluster results
        clusters = []
        for cluster_row in cluster_rows:
            cluster_id = cluster_row["id"]

            # Get incident IDs for this cluster
            cursor = conn.execute(
                "SELECT incident_id FROM cluster_members WHERE cluster_id = ?",
                (cluster_id,),
            )
            incident_ids = [r["incident_id"] for r in cursor.fetchall()]

            clusters.append(
                ClusterResult(
                    cluster_id=cluster_row["cluster_label"],
                    incident_ids=incident_ids,
                    size=len(incident_ids),
                    summary=cluster_row["summary"],
                    centroid_text=cluster_row["centroid_text"],
                )
            )

        # Calculate metrics
        calc = MetricsCalculator(conn)
        metrics = calc.calculate()

        # Generate executive summary
        ollama = OllamaClient()
        try:
            summarizer = ClusterSummarizer(ollama, conn)
            try:
                executive_summary = await summarizer.generate_executive_summary(
                    quarter=request.quarter_label,
                    metrics=metrics,
                    clusters=clusters,
                )
            except (OllamaUnavailableError, OllamaModelNotFoundError) as error:
                executive_summary = _fallback_executive_summary(
                    quarter=request.quarter_label,
                    metrics=metrics,
                    clusters=clusters,
                    error=error,
                )
        finally:
            await ollama.close()

        # Create report record
        report_id = str(uuid4())
        report = ReportResult(
            report_id=report_id,
            cluster_run_id=request.cluster_run_id,
            title=request.title,
            executive_summary=executive_summary,
            metrics=metrics,
            created_at=datetime.now(timezone.utc).isoformat(),
            docx_path=None,
        )

        # Generate DOCX file
        output_dir = Path.home() / ".incident-workbench" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{report_id}.docx"

        generator = DocxGenerator()
        generator.generate(report, clusters, request.chart_pngs, str(output_path))

        report.docx_path = str(output_path)

        # Store in database
        conn.execute(
            """
            INSERT INTO reports (id, cluster_run_id, title, executive_summary,
                               metrics_json, created_at, docx_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.report_id,
                report.cluster_run_id,
                report.title,
                report.executive_summary,
                metrics.model_dump_json(),
                report.created_at,
                report.docx_path,
            ),
        )
        conn.commit()

        return {"report_id": report.report_id, "docx_path": report.docx_path}

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@router.get("")
async def list_reports() -> list[ReportResult]:
    """List all generated reports."""
    conn = db.get_connection()

    try:
        cursor = conn.execute(
            """
            SELECT id, cluster_run_id, title, executive_summary,
                   metrics_json, created_at, docx_path
            FROM reports
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()

        reports = []
        for row in rows:
            metrics = MetricsResult(**json.loads(row["metrics_json"]))
            reports.append(
                ReportResult(
                    report_id=row["id"],
                    cluster_run_id=row["cluster_run_id"],
                    title=row["title"],
                    executive_summary=row["executive_summary"],
                    metrics=metrics,
                    created_at=row["created_at"],
                    docx_path=row["docx_path"],
                )
            )

        return reports

    finally:
        conn.close()


@router.get("/{report_id}/download")
async def download_report(report_id: str) -> FileResponse:
    """Download a generated report."""
    conn = db.get_connection()

    try:
        cursor = conn.execute("SELECT docx_path, title FROM reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()

        if not row or not row["docx_path"]:
            raise HTTPException(status_code=404, detail="Report not found")

        docx_path = row["docx_path"]
        if not os.path.exists(docx_path):
            raise HTTPException(status_code=404, detail="DOCX file not found on disk")

        # Create filename from report title
        filename = f"{row['title'].replace(' ', '_')}_{report_id[:8]}.docx"

        return FileResponse(
            path=docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filename,
        )

    finally:
        conn.close()
