"""Test Phase 4: LLM Summary & DOCX Export."""

import base64
import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from database import db
from exceptions import OllamaUnavailableError
from main import app
from models.cluster import ClusterResult
from models.report import MetricsResult, ReportResult
from services.docx_generator import DocxGenerator
from services.ollama_client import OllamaClient

client = TestClient(app)


def create_test_png() -> str:
    """Create a simple test PNG and return base64 encoded."""
    # Create a simple red square image
    img = Image.new("RGB", (400, 300), color="red")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def test_docx_generation():
    """Test DOCX report generation with mock data."""
    print("Testing DOCX Generation...")

    # Create test metrics
    metrics = MetricsResult(
        total_incidents=50,
        sev1_count=5,
        sev2_count=15,
        sev3_count=20,
        sev4_count=10,
        unknown_count=0,
        mean_resolution_hours=24.5,
        median_resolution_hours=18.2,
        p50_resolution_hours=18.2,
        p90_resolution_hours=48.7,
        by_severity={"SEV1": 5, "SEV2": 15, "SEV3": 20, "SEV4": 10},
        by_month={"2024-01": 12, "2024-02": 18, "2024-03": 20},
    )

    # Create test clusters
    clusters = [
        ClusterResult(
            cluster_id=0,
            incident_ids=[1, 2, 3, 4, 5],
            size=5,
            summary="Database Connection Failures",
            centroid_text="Multiple incidents related to PostgreSQL connection timeouts during peak traffic hours.",
        ),
        ClusterResult(
            cluster_id=1,
            incident_ids=[6, 7, 8],
            size=3,
            summary="API Gateway Timeouts",
            centroid_text="API requests timing out due to upstream service degradation.",
        ),
        ClusterResult(
            cluster_id=2,
            incident_ids=[9, 10, 11, 12],
            size=4,
            summary="Memory Leak in Worker Processes",
            centroid_text="Worker processes consuming excessive memory over time, requiring restarts.",
        ),
    ]

    # Create test report
    report = ReportResult(
        report_id="test-report-001",
        cluster_run_id="test-run-001",
        title="Q1 2024 Incident Review",
        executive_summary=(
            "During Q1 2024, the engineering team responded to 50 incidents across "
            "all severity levels. The majority of incidents (70%) were SEV3 or lower, "
            "indicating effective preventive measures for critical systems.\n\n"
            "Mean resolution time stood at 24.5 hours, with the median at 18.2 hours, "
            "suggesting a few outlier incidents skewed the average upward. The 90th "
            "percentile resolution time of 48.7 hours indicates most incidents are "
            "resolved within two business days.\n\n"
            "Three major incident clusters emerged: database connection failures during "
            "peak hours, API gateway timeouts, and memory leaks in worker processes. "
            "These patterns suggest infrastructure scaling and resource management should "
            "be priorities for Q2.\n\n"
            "Recommended actions include implementing connection pooling improvements, "
            "upgrading API gateway capacity, and conducting memory profiling on worker "
            "services."
        ),
        metrics=metrics,
        created_at="2024-04-01T12:00:00Z",
    )

    # Create test charts
    chart_pngs = {
        "incidents_by_severity": create_test_png(),
        "resolution_time_trend": create_test_png(),
        "incidents_by_month": create_test_png(),
    }

    # Generate DOCX
    output_dir = Path.home() / ".incident-workbench" / "reports" / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "test_report.docx"

    generator = DocxGenerator()
    result_path = generator.generate(report, clusters, chart_pngs, str(output_path))

    # Verify file exists
    assert os.path.exists(result_path), f"DOCX file not created at {result_path}"

    file_size = os.path.getsize(result_path)
    print(f"✓ DOCX generated successfully: {result_path}")
    print(f"  File size: {file_size:,} bytes")
    print(f"  Sections: Title, Executive Summary, Metrics, 3 Charts, 3 Clusters")


def test_database_migration():
    """Test that the reports table has correct schema."""
    print("\nTesting Database Schema...")

    conn = db.get_connection()
    try:
        # Run migrations
        db.run_migrations()

        # Check table exists with correct columns
        cursor = conn.execute("PRAGMA table_info(reports)")
        columns = {row["name"]: row["type"] for row in cursor.fetchall()}

        expected_columns = {
            "id": "TEXT",
            "cluster_run_id": "TEXT",
            "title": "TEXT",
            "executive_summary": "TEXT",
            "metrics_json": "TEXT",
            "created_at": "TEXT",
            "docx_path": "TEXT",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} missing"
            assert columns[col_name] == col_type, (
                f"Column {col_name} has type {columns[col_name]}, expected {col_type}"
            )

        print("✓ Database schema correct")
        print(f"  Columns: {', '.join(columns.keys())}")

    finally:
        conn.close()


def test_report_generation_falls_back_without_ollama(monkeypatch):
    """Report generation should succeed with deterministic fallback if Ollama is unavailable."""
    run_id = str(uuid4())
    external_id = f"phase4-fallback-{run_id}"

    conn = db.get_connection()
    try:
        incident_cursor = conn.execute(
            """
            INSERT INTO incidents (
                external_id, source, severity, title, description,
                occurred_at, resolved_at, raw_data, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                external_id,
                "slack_export",
                "SEV2",
                "Fallback test incident",
                "Incident seeded for fallback report generation test.",
                "2024-01-15T10:30:00Z",
                "2024-01-15T11:00:00Z",
                '{"seeded": true}',
                "resolved",
            ),
        )
        incident_id = incident_cursor.lastrowid

        conn.execute(
            """
            INSERT INTO cluster_runs (id, n_clusters, method, parameters)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, 1, "manual-test", '{"seeded": true}'),
        )

        cluster_cursor = conn.execute(
            """
            INSERT INTO clusters (run_id, cluster_label, summary, centroid_text)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, 0, "Fallback cluster", "Synthetic cluster for fallback path."),
        )
        cluster_id = cluster_cursor.lastrowid

        conn.execute(
            """
            INSERT INTO cluster_members (cluster_id, incident_id, distance_to_centroid)
            VALUES (?, ?, ?)
            """,
            (cluster_id, incident_id, 0.0),
        )
        conn.commit()
    finally:
        conn.close()

    async def mock_generate(*_args, **_kwargs):
        raise OllamaUnavailableError("mocked unavailable")

    monkeypatch.setattr(OllamaClient, "generate", mock_generate)

    response = client.post(
        "/reports/generate",
        json={
            "cluster_run_id": run_id,
            "title": "Fallback Report Test",
            "quarter_label": "Q1 2024",
            "chart_pngs": {"seed_chart": create_test_png()},
        },
    )

    assert response.status_code == 200, response.text
    report_id = response.json()["report_id"]

    reports = client.get("/reports")
    assert reports.status_code == 200
    report = next((r for r in reports.json() if r["report_id"] == report_id), None)
    assert report is not None
    assert "generated without Ollama" in report["executive_summary"]

    cleanup_conn = db.get_connection()
    try:
        cleanup_conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        cleanup_conn.execute("DELETE FROM cluster_members WHERE cluster_id IN (SELECT id FROM clusters WHERE run_id = ?)", (run_id,))
        cleanup_conn.execute("DELETE FROM clusters WHERE run_id = ?", (run_id,))
        cleanup_conn.execute("DELETE FROM cluster_runs WHERE id = ?", (run_id,))
        cleanup_conn.execute("DELETE FROM incidents WHERE external_id = ? AND source = ?", (external_id, "slack_export"))
        cleanup_conn.commit()
    finally:
        cleanup_conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Testing: LLM Summary & DOCX Export")
    print("=" * 60)

    test_database_migration()
    test_docx_generation()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    print("\nGenerated test report in ~/.incident-workbench/reports/test/test_report.docx")
    print("Open the file in Pages/Word to verify formatting.")
