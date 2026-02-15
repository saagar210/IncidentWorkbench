"""Test Phase 4: LLM Summary & DOCX Export."""

import base64
import os
from io import BytesIO
from pathlib import Path

from PIL import Image

from database import db
from models.cluster import ClusterResult
from models.report import MetricsResult, ReportResult
from services.docx_generator import DocxGenerator


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
        cluster_run_id=1,
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

    return result_path


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
            "cluster_run_id": "INTEGER",
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


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Testing: LLM Summary & DOCX Export")
    print("=" * 60)

    test_database_migration()
    docx_path = test_docx_generation()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    print(f"\nGenerated test report: {docx_path}")
    print("Open the file in Pages/Word to verify formatting.")
