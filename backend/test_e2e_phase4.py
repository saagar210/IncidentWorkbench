"""End-to-end test for Phase 4: Generate report from real cluster run."""

import base64
import os
import sqlite3
import time
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
import requests
from PIL import Image

BASE_URL = "http://127.0.0.1:8765"
RUN_E2E = os.getenv("RUN_E2E_PHASE4") == "1"
pytestmark = pytest.mark.integration


def create_test_chart_png() -> str:
    """Create a test chart PNG."""
    img = Image.new("RGB", (800, 600), color="#3b82f6")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def _seed_cluster_run_if_missing() -> str:
    """Create minimal incident+cluster data so E2E always exercises report generation."""
    run_id = str(uuid4())
    db_path = Path.home() / ".incident-workbench" / "incidents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row

        now = int(time.time())
        occurred_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 3600))
        resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 1800))

        conn.execute(
            """
            INSERT INTO incidents (
                external_id, source, severity, title, description,
                occurred_at, resolved_at, raw_data, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_id, source) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                resolved_at = excluded.resolved_at,
                raw_data = excluded.raw_data,
                status = excluded.status
            """,
            (
                f"e2e-{run_id}",
                "slack_export",
                "SEV2",
                "E2E seeded incident",
                "Seeded incident to validate live report generation path.",
                occurred_at,
                resolved_at,
                '{"seeded": true}',
                "resolved",
            ),
        )

        incident_row = conn.execute(
            "SELECT id FROM incidents WHERE external_id = ? AND source = ?",
            (f"e2e-{run_id}", "slack_export"),
        ).fetchone()
        assert incident_row is not None, "Failed to create seeded incident"
        incident_id = incident_row[0]

        conn.execute(
            """
            INSERT INTO cluster_runs (id, n_clusters, method, parameters)
            VALUES (?, ?, ?, ?)
            """,
            (
                run_id,
                1,
                "manual-seed",
                '{"seeded": true, "linkage": "average", "metric": "cosine"}',
            ),
        )

        cluster_cursor = conn.execute(
            """
            INSERT INTO clusters (run_id, cluster_label, summary, centroid_text)
            VALUES (?, ?, ?, ?)
            """,
            (
                run_id,
                0,
                "Seeded incident cluster",
                "Synthetic cluster for e2e report generation validation.",
            ),
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
        return run_id
    finally:
        conn.close()


def _ensure_test_admin() -> tuple[str, str]:
    """Seed deterministic E2E admin credentials in local SQLite."""
    username = "test-admin"
    password = "test-only-password"
    db_path = Path.home() / ".incident-workbench" / "incidents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        from security.auth import hash_password

        password_hash = hash_password(password)
        if row is None:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, roles)
                VALUES (?, ?, ?)
                """,
                (username, password_hash, '["admin"]'),
            )
        else:
            conn.execute(
                """
                UPDATE users
                SET password_hash = ?, roles = ?
                WHERE id = ?
                """,
                (password_hash, '["admin"]', row["id"]),
            )
        conn.commit()
    finally:
        conn.close()

    return username, password


@pytest.mark.skipif(
    not RUN_E2E,
    reason="Set RUN_E2E_PHASE4=1 and start backend on 127.0.0.1:8765 to run this test",
)
def test_e2e_report_generation():
    """Test complete report generation flow."""
    print("=" * 60)
    print("Phase 4 E2E Test: Report Generation")
    print("=" * 60)
    session = requests.Session()

    # Step 1: Check health
    print("\n1. Checking backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
    except requests.ConnectionError as exc:
        pytest.skip(f"Backend is not running at {BASE_URL}: {exc}")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    health = response.json()
    print(f"   ✓ Backend is healthy: {health['status']}")
    print(f"   Database: {health['database']}")

    # Seed deterministic admin credentials for privileged endpoint tests.
    username, password = _ensure_test_admin()
    login_response = session.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=20,
    )
    assert login_response.status_code == 200, f"Auth login failed: {login_response.text}"
    csrf_token = session.cookies.get("__Host-csrf") or session.cookies.get("workbench-csrf")
    assert csrf_token, "CSRF cookie missing after login"

    # Step 2: Get cluster runs
    print("\n2. Fetching cluster runs...")
    response = session.get(f"{BASE_URL}/clusters")
    assert response.status_code == 200, f"Failed to fetch cluster runs: {response.text}"
    runs = response.json()

    if not runs:
        print("   ⚠️  No cluster runs found. Seeding one for E2E coverage...")
        seeded_run_id = _seed_cluster_run_if_missing()
        response = session.get(f"{BASE_URL}/clusters")
        assert response.status_code == 200, f"Failed to re-fetch cluster runs: {response.text}"
        runs = response.json()
        latest_run = next((run for run in runs if run["run_id"] == seeded_run_id), runs[0])
        print(f"   ✓ Seeded cluster run: {latest_run['run_id']}")
    else:
        latest_run = runs[0]
    print(f"   ✓ Found {len(runs)} cluster run(s)")
    print(f"   Latest run: {latest_run['run_id']} with {latest_run['n_clusters']} clusters")

    # Step 3: Generate test charts
    print("\n3. Generating test chart PNGs...")
    chart_pngs = {
        "severity_breakdown": create_test_chart_png(),
        "monthly_trend": create_test_chart_png(),
        "mttr_by_severity": create_test_chart_png(),
    }
    print(f"   ✓ Generated {len(chart_pngs)} chart images")

    # Step 4: Generate report
    print("\n4. Generating DOCX report...")

    request_data = {
        "cluster_run_id": latest_run["run_id"],
        "title": "Q1 2024 Incident Review (E2E Test)",
        "quarter_label": "Q1 2024",
        "chart_pngs": chart_pngs,
    }

    start_time = time.time()
    response = session.post(
        f"{BASE_URL}/reports/generate",
        json=request_data,
        headers={"X-CSRF-Token": csrf_token},
    )
    elapsed = time.time() - start_time

    assert response.status_code == 200, f"Report generation failed: {response.text}"
    result = response.json()

    print(f"   ✓ Report generated in {elapsed:.1f}s")
    print(f"   Report ID: {result['report_id']}")
    print(f"   DOCX Path: {result['docx_path']}")

    # Step 5: List reports
    print("\n5. Listing all reports...")
    response = session.get(f"{BASE_URL}/reports")
    assert response.status_code == 200, f"Failed to list reports: {response.text}"
    reports = response.json()
    print(f"   ✓ Found {len(reports)} report(s)")

    # Verify our report is in the list
    our_report = next((r for r in reports if r["report_id"] == result["report_id"]), None)
    assert our_report is not None, "Generated report not found in list"
    print(f"   Title: {our_report['title']}")
    print(f"   Incidents: {our_report['metrics']['total_incidents']}")
    print(f"   Executive Summary (first 150 chars): {our_report['executive_summary'][:150]}...")

    # Step 6: Download report
    print("\n6. Testing report download...")
    response = session.get(f"{BASE_URL}/reports/{result['report_id']}/download")
    assert response.status_code == 200, f"Download failed: {response.status_code}"
    assert (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        in response.headers.get("content-type", "")
    ), "Invalid content type for DOCX"
    print(f"   ✓ Downloaded {len(response.content):,} bytes")
    print(f"   Content-Type: {response.headers.get('content-type')}")

    print("\n" + "=" * 60)
    print("✓ All E2E tests passed!")
    print("=" * 60)
    print(f"\nReport available at: {BASE_URL}/reports/{result['report_id']}/download")


if __name__ == "__main__":
    try:
        test_e2e_report_generation()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
